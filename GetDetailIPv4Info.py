"""
The MIT License (MIT)

Copyright (c) 2024 ChocolaMilk92

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import json
import urllib3

class GetDetailIPv4Info:
    def __init__(self, ip_address: str = "json") -> None:
        self.ip_address = ip_address
        https = urllib3.PoolManager()
        url = f'https://ipinfo.io/{self.ip_address}'
        try:
            response = https.request('GET', url)
            self.all_data = json.loads(response.data)
        except Exception as e:
            raise e
        
    def __repr__(self):
        return str(self.all_data)
        
    @property
    def all(self):  # Returns all information as a dictionary
        return self.all_data
    
    @property
    def hostname(self):  # Returns the hostname associated with the IP
        if "hostname" in self.all_data:
            return self.all_data["hostname"]
        return None
    
    @property
    def ip(self):  # Returns the IP address
        if "ip" in self.all_data:
            return self.all_data["ip"]
        return None
    
    @property
    def city(self):  # Returns the city of the IP belongs to
        if "city" in self.all_data:
            return self.all_data["city"]
        return None
    
    @property
    def region(self):  # Returns the region of the IP belongs to
        if "region" in self.all_data:
            return self.all_data["region"]
        return None
    
    @property
    def country(self):  # Returns the country of the IP belongs to
        if "country" in self.all_data:
            return self.all_data["country"]
        return None
    
    @property
    def location(self):  # Returns latitude and longitude
        if "loc" in self.all_data:
            latitude, longitude = float(self.all_data["loc"].split(",")[0]), float(self.all_data["loc"].split(",")[1])
            return (latitude, longitude)
        return None
    
    @property
    def organization(self):  # Returns the organization of the IP belongs to
        if "org" in self.all_data:
            return self.all_data["org"]
        return None
    
    @property
    def postal(self):  # Returns the postal code of the IP
        if "postal" in self.all_data:
            return self.all_data["postal"]
        return None
    
    @property
    def timezone(self):  # Returns the timezone of the IP
        if "timezone" in self.all_data:
            return self.all_data["timezone"]
        return None
    
    @property
    def bogon(self):  # Checks if the IP is a bogon address
        if "bogon" in self.all_data:
            return self.all_data["bogon"]
        return None

