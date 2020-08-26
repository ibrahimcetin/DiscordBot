import json

import aiohttp


class RestDB:
    def connect(self, url: str, api_key: str):
        self.url = url

        self.headers = {
            'content-type': "application/json",
            'x-apikey': api_key,
            'cache-control': "no-cache"
        }

    async def getDocument(self, member_id: str = None):
        payload = {"q": json.dumps({"member_id": member_id})} if member_id else None

        async with aiohttp.ClientSession() as session:
            async with session.request("GET", self.url, params=payload, headers=self.headers) as response:
                if response.status == 200:
                    json_data = await response.json()

                    if len(json_data) == 0:
                        return False
                    elif len(json_data) == 1:
                        return json_data[0]
                    else:
                        return json_data

                else:
                    return False

    async def newDocument(self, data: dict):
        payload = json.dumps(data)

        async with aiohttp.ClientSession() as session:
            async with session.request("GET", self.url, params={"q": json.dumps({data["member_id"]: {"$exists": True}})}, headers=self.headers) as response:
                if response.status == 200:
                    exists = await response.json()

        if not exists:
            async with aiohttp.ClientSession() as session:
                async with session.request("POST", self.url, data=payload, headers=self.headers) as response:
                    if response.status == 201:
                        json_data = await response.json()
                        return json_data
                    else:
                        return False
        else:
            return False

    async def updateDocument(self, object_id: str, data: dict):
        url = f"{self.url}/{object_id}"
        payload = json.dumps(data)

        async with aiohttp.ClientSession() as session:
            async with session.request("PUT", url, data=payload, headers=self.headers) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data
                else:
                    return False

    async def deleteDocument(self, object_id: str):
        url = f"{self.url}/{object_id}"

        async with aiohttp.ClientSession() as session:
            async with session.request("DELETE", url, headers=self.headers) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data
                else:
                    return False
