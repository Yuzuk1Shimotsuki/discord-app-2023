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
import pytz
import urllib3
from datetime import datetime

class GetDetailIPv4Info:
    """
    Getting detail information from a IPv4 address.

    Parameters
    ----------
    ip_adress: str
        The IP address to get information

    Returns
    -------
    dict:
        Dictonary of all relevant information(s) of the IP address.
    """
    def __init__(self, ip_address: str = "json") -> None:
        self.ip_address = ip_address
        https = urllib3.PoolManager()
        url = f'https://ipinfo.io/{self.ip_address}'
        try:
            response = https.request('GET', url)
            self.all_data = json.loads(response.data)
            # Handling error
            if "status" in self.all_data:
                error = self.all_data["error"]
                raise ValueError(f"{self.all_data["status"]} {error["title"]}: {error["message"]}")
        except Exception as e:
            raise e
        
    def __repr__(self):
        return str(self.all_data)
        
    @property
    def all(self) -> str:
        "Returns all information as a dictionary"
        return self.all_data
    
    @property
    def hostname(self) -> str:
        "Returns the hostname associated with the IP"
        if "hostname" in self.all_data:
            return self.all_data["hostname"]
        return None

    @property
    def ip(self) -> str:
        "Returns the IP address"
        if "ip" in self.all_data:
            return self.all_data["ip"]
        return None
    
    @property
    def city(self) -> str:
        "Returns the city of the IP belongs to"
        if "city" in self.all_data:
            return self.all_data["city"]
        return None
    
    @property
    def region(self) -> str:
        "Returns the region of the IP belongs to"
        if "region" in self.all_data:
            return self.all_data["region"]
        return None
    
    @property
    def country(self) -> str:
        "Returns the country of the IP belongs to"
        if "country" in self.all_data:
            return self.all_data["country"]
        return None
    
    @property
    def location(self) -> tuple:
        "Returns the latitude and longitude information of the IP"
        if "loc" in self.all_data:
            latitude, longitude = self.all_data["loc"].split(",")[0], self.all_data["loc"].split(",")[1]
            return (latitude, longitude)
        return None
    
    @property
    def organization(self) -> str:
        "Returns the organization of the IP belongs to"
        if "org" in self.all_data:
            return self.all_data["org"]
        return None
    
    @property
    def postal(self) -> str:
        "Returns the postal code of the IP"
        if "postal" in self.all_data:
            return self.all_data["postal"]
        return None
    
    @property
    def time(self) -> datetime:
        "Returns the current UTC time of the IP"
        if "timezone" in self.all_data:
            return datetime.now(pytz.timezone(self.all_data["timezone"]))
        return None

    @property
    def timezone(self) -> str:
        "Returns the timezone of the IP"
        if "timezone" in self.all_data:
            return self.all_data["timezone"]
        return None
    
    @property
    def bogon(self) -> bool:
        "Checks if the IP is a bogon address"
        if "bogon" in self.all_data:
            return self.all_data["bogon"]
        return None


