# File location: business/management/commands/update_listing_locations.py

from django.core.management.base import BaseCommand
from business.models import Listing
from users.models import BusinessRegistration
import requests
import time


class Command(BaseCommand):
    help = 'Update existing listings with location data from business registrations'

    def geocode_address(self, address_string):
        """Geocode an address string to lat/lng"""
        if not address_string or not address_string.strip():
            return None
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address_string,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'LastBite-App/1.0'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                address_details = result.get('address', {})
                
                street_number = address_details.get('house_number', '')
                street = address_details.get('road', '')
                street_address = f"{street_number} {street}".strip() if street_number else street
                
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'address': street_address or address_details.get('street', ''),
                    'city': address_details.get('city') or address_details.get('town') or address_details.get('village', ''),
                    'state': address_details.get('state', ''),
                    'zip_code': address_details.get('postcode', '')
                }
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Geocoding error: {e}"))
        
        return None

    def handle(self, *args, **options):
        # Get all listings without location data
        listings_without_location = Listing.objects.filter(
            latitude__isnull=True
        ) | Listing.objects.filter(
            longitude__isnull=True
        )
        
        total_listings = listings_without_location.count()
        self.stdout.write(self.style.WARNING(f"Found {total_listings} listings without location data"))
        
        updated_count = 0
        failed_count = 0
        
        for listing in listings_without_location:
            # Get business registration for this owner
            try:
                business = BusinessRegistration.objects.filter(user=listing.owner).first()
                
                if not business or not business.address:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Listing {listing.id} ({listing.title}): No business location found")
                    )
                    failed_count += 1
                    continue
                
                # Geocode the business location
                self.stdout.write(f"Processing listing {listing.id}: {listing.title}")
                self.stdout.write(f"  Business location: {business.address}")
                
                location_data = self.geocode_address(business.address)
                
                if location_data:
                    listing.latitude = location_data['latitude']
                    listing.longitude = location_data['longitude']
                    listing.address = location_data['address']
                    listing.city = location_data['city']
                    listing.state = location_data['state']
                    listing.zip_code = location_data['zip_code']
                    listing.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Updated listing {listing.id}: "
                            f"{location_data['latitude']}, {location_data['longitude']}"
                        )
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to geocode: {business.address}")
                    )
                    failed_count += 1
                
                # Be nice to Nominatim API - rate limit to 1 request per second
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing listing {listing.id}: {e}")
                )
                failed_count += 1
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully updated: {updated_count} listings"))
        self.stdout.write(self.style.ERROR(f"✗ Failed: {failed_count} listings"))
        self.stdout.write("="*50)