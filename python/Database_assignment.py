import requests
import xmltodict
from math import radians, sin, cos, sqrt, atan2
from pyproj import Transformer


#서로 다른 위치의 위도, 경도를 알때 두 점 사이의 거리를 반환해주는 함수
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

#내 위치의 위도, 경도를 알려주는 코드. target 위도, 경도가 된다.
def getGeoCode(address, client_id, client_secret):
    header = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret
    }
    
    endpoint = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    url = f"{endpoint}?query={address}"
    
    res = requests.get(url, headers=header)
    return res



if __name__ == '__main__':
    # 주소와 인증키 설정
    address = "서울특별시 성동구 서울숲2길 32-14"
    client_id = 'ttudos8cc0'
    client_secret = 'zEIKk9phr1yoo9lElkso95KiEifmHyVvV516W7kx'

    # 지정한 주소의 위도 경도 가져오기
    response = getGeoCode(address, client_id, client_secret)
    
    if response.status_code == 200:
        result = response.json()    
        target_coordinates = (float(result['addresses'][0]['y']), float(result['addresses'][0]['x']))
        
        # 충전소 정보 가져오기
        url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo'
        
        #총 3페이지가 있음
        params1 = {
            'serviceKey': 'SSNDojDBnt4vUKsjgURAm342jCB5xNa15HGEFJ9IzlcB+A40MLb5ozuW++FWu4u04zIZfk/XvLzh3IaedMHa2g==',
            'pageNo': '1',
            'numOfRows': '9999',
            'zscode' : '11200'
        }
        
        
        params2 = {
            'serviceKey': 'SSNDojDBnt4vUKsjgURAm342jCB5xNa15HGEFJ9IzlcB+A40MLb5ozuW++FWu4u04zIZfk/XvLzh3IaedMHa2g==',
            'pageNo': '2',
            'numOfRows': '5000',
            'zscode' : '11200'
        }
        
        params3 = {
            'serviceKey': 'SSNDojDBnt4vUKsjgURAm342jCB5xNa15HGEFJ9IzlcB+A40MLb5ozuW++FWu4u04zIZfk/XvLzh3IaedMHa2g==',
            'pageNo': '3',
            'numOfRows': '2000',
            'zscode' : '11200'
        }
        
        response1 = requests.get(url, params=params1)
        response2 = requests.get(url, params=params2)
        response3 = requests.get(url, params=params3)
        
        responses = [response1, response2, response3]
        dics = [xmltodict.parse(response.content) for response in responses]


        #페이지별로 각각 돌려줌
        for dic in dics:
            if 'response' in dic and 'body' in dic['response'] and 'items' in dic['response']['body']:
                items = dic['response']['body']['items']['item']

                # 충전소 좌표를 리스트로 저장, charger의 위도, 경도 저장
                charger_coordinates = [(float(charger['lat']), float(charger['lng'])) for charger in items]

                # 거리 계산 및 가장 가까운 5개의 충전소 찾기
                distances = [
                    (charger_idx, haversine(target_coordinates[0], target_coordinates[1], charger[0], charger[1]))
                    for charger_idx, charger in enumerate(charger_coordinates)
                ]

                # 중복된 좌표를 저장할 set
                unique_coordinates = set()

                # 가장 가까운 5개의 충전소 출력
                closest_chargers = []
                for charger_idx, distance in sorted(distances, key=lambda x: x[1]):
                    charger_info = items[charger_idx]
                    latitude = float(charger_info.get('lat', 0))
                    longitude = float(charger_info.get('lng', 0))

                    # 좌표가 중복되지 않으면 결과에 추가하고 set에 좌표 추가
                    if (latitude, longitude) not in unique_coordinates:
                        unique_coordinates.add((latitude, longitude))
                        closest_chargers.append({'index': charger_idx, 'distance': distance, 'charger_info': charger_info})

                    # 5개 이상의 결과가 있다면 루프 종료
                    if len(closest_chargers) == 5:
                        break

                # 결과 출력
                for charger in closest_chargers:
                    distance = charger['distance']
                    charger_info = charger['charger_info']
                    statNm = charger_info.get('statNm', 'N/A')  
                    addr = charger_info.get('addr', 'N/A')  
                    latitude = float(charger_info.get('lat', 0))
                    longitude = float(charger_info.get('lng', 0))
                    print("---------------------------------------------------------------------")
                    print(f"\033[1mDistance: {distance:.2f} km\033[0m")
                    print(f"\033[1mCharger Name: {statNm}\033[0m")
                    print(f"\033[1mAddress: {addr}\033[0m")
                    #print(f"Latitude: {latitude}")
                    #print(f"Longitude: {longitude}")
                    print("---------------------------------------------------------------------")

                    # 서울특별시 성동구 휴게음식점 정보 가져오기
                    base_url = 'http://openapi.seoul.go.kr:8088/575a59534463737933354451507347/xml/LOCALDATA_072405/'
                    #중부원점정보
                    source_crs = '+proj=tmerc +lat_0=38 +lon_0=127.0028902777778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43'
                    #위도,경도정보
                    target_crs = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
                    start_page = 1
                    #json file row 개수
                    end_page = 127274
                    #데이터반환이 1000개로 제한되어 있기때문에 1000단위로 반복
                    page_size = 1000
                    sung_dong = []

                    # 좌표 변환을 위한 Transformer 객체 생성
                    transformer = Transformer.from_crs(source_crs, target_crs)

                    #127274개를 1000개씩 돌려가면서 비교해준다
                    for start in range(start_page, end_page + 1, page_size):
                        end = min(start + page_size - 1, end_page)
                        url = f'{base_url}{start}/{end}/'

                        response = requests.get(url)
                        content = response.content
                        dic = xmltodict.parse(content)

                        if 'LOCALDATA_072405' in dic and 'row' in dic['LOCALDATA_072405']:
                            items = dic['LOCALDATA_072405']['row']

                            for i in items:
                                #중부원점 좌표, 도로명주소가 존재하고 주소가 서울특별시 성동구이면
                                if i.get('X') and i.get('Y') and i.get('SITEWHLADDR') and i['SITEWHLADDR'].startswith('서울특별시 성동구'):
                                    #중부원점좌표 저장
                                    x, y = float(i['X']), float(i['Y'])
                                    
                                    # 중부원점 좌표를 위도,경도 좌표 변환 수행
                                    lon, lat = transformer.transform(x, y)
                                    
                                    #반환된 위도,경도, 도로명주소, 가게이름을 리스트에 저장
                                    sung_dong.append([lat, lon, i['SITEWHLADDR'],i['BPLCNM']])

                        else:
                            print(f"Error for {start}-{end}: {dic}")

                    # 서울특별시 성동구 휴게음식점과의 거리 계산 및 500m 이내의 음식점 출력
                    for coords in sung_dong:
                        food_distance = haversine(latitude, longitude, coords[0], coords[1])
                        # 500m 이내의 음식점 출력
                        if food_distance <= 0.5: 
                            print(f"Distance from Charger to Food: {food_distance:.2f} km")
                            print(f"Food Location: {coords[2]}")
                            print(f"restaurant name: {coords[3]}")
                            print()
                        
            else:
                print(f"Error: {dic}")
                pass
    else:
        print(f'Error code: {response}')
        pass