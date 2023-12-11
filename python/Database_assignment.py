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
            'numOfRows': '2459',
            'zscode' : '11200'
        }
        
        
        params3 = {
            'serviceKey': 'SSNDojDBnt4vUKsjgURAm342jCB5xNa15HGEFJ9IzlcB+A40MLb5ozuW++FWu4u04zIZfk/XvLzh3IaedMHa2g==',
            'pageNo': '3',
            'numOfRows': '1129',
            'zscode' : '11200'
        }
        
        response1 = requests.get(url, params=params1)
        response2 = requests.get(url, params=params2)
        response3 = requests.get(url, params=params3)
        
        
        responses = [response1, response2, response3]
        dics = [xmltodict.parse(response.content) for response in responses]
        
        #전체 페이지에 대해 가장 가까운 거리 정보가 담겨져 있는 리스트
        final_distance = []
        
        # 중복된 좌표를 저장할 set
        unique_coordinates = set()

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

                
                

                # 각 페이지별로 가장 가까운 충전소 5개를 저장할 리스트
                closest_chargers_by_page = []
                for charger_idx, distance in sorted(distances, key=lambda x: x[1]):
                    charger_info = items[charger_idx]
                    latitude = float(charger_info.get('lat', 0))
                    longitude = float(charger_info.get('lng', 0))

                    # 좌표가 중복되지 않으면 결과에 추가하고 set에 좌표 추가
                    if (latitude, longitude) not in unique_coordinates:
                        unique_coordinates.add((latitude, longitude))
                        #페이지별로 가장가까운 거리 5개를 선별함
                        closest_chargers_by_page.append({'index': charger_idx, 'distance': distance, 'charger_info': charger_info})
                        
                        #이것은 전체 페이지 거리가 들어있음. 총 3페이지고 각 페이지 별로 5개씩 뽑아 냈으니까 15개의 정보가 저장되어 있음.
                        final_distance.append({'index': charger_idx, 'distance': distance, 'charger_info': charger_info})

                    # 각 페이지별로 5개 이상의 결과가 있다면 루프 종료
                    if len(closest_chargers_by_page) == 5:
                        break

                # 결과 출력
                #for charger in closest_chargers_by_page:
                #    pass
                   
            else:
                print(f"Error: {dic}")
            
    else:
        print(f'Error code: {response}')
    
            
  ##################################################################################################################################################################
    #각 페이지별로 가까운 거리 5개씩 저장, 따라서  총 3페이지니까 15개의 거리가 저장되어있음. 그 중 가장 가까운 거리 5개 선별               
    sorted_distances = sorted(final_distance, key=lambda x: x['distance'])
    
    #가장 가까운 거리 5개 선별
    top_5_closest_distances = sorted_distances[:5]
    
    #내 위치랑 가장 가까운 충전소 5개의  거리, 충전소 이름, 도로명주소를 출력
    for charger in top_5_closest_distances:
        distance = charger['distance']
        charger_info = charger['charger_info']
        statNm = charger_info.get('statNm', 'N/A')  
        addr = charger_info.get('addr', 'N/A')  
        #음식점과의 거리를 구하기위해 따로 위도, 경도를 저장해준다
        latitude = float(charger_info.get('lat', 0))
        
        #음식점과의 거리를 구하기위해 따로 위도, 경도를 저장해준다
        longitude = float(charger_info.get('lng', 0))
        
        print("---------------------------------------------------------------------")
        print(f"\033[1mDistance: {distance:.2f} km\033[0m")
        print(f"\033[1mCharger Name: {statNm}\033[0m")
        print(f"\033[1mAddress: {addr}\033[0m")
        #print(f"Latitude: {latitude}")
        #print(f"Longitude: {longitude}")
        print("---------------------------------------------------------------------")
        
        
        
        base_url = 'http://openapi.seoul.go.kr:8088/575a59534463737933354451507347/xml/LOCALDATA_072405/'
        #중부원점정보
        source_crs = '+proj=tmerc +lat_0=38 +lon_0=127.0028902777778 +k=1 +x_0=200000 +y_0=500000 +ellps=bessel +units=m +no_defs +towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43'
        #위도,경도정보
        target_crs = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
        start_page = 1
        #json file row 개수
        end_page = 70000
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
            #선별된 충전소 5개와 충전소 근처에 있는 음식점 거리를 출력
            food_distance = haversine(latitude, longitude, coords[0], coords[1])
            # 300m 이내의 음식점 출력
            if food_distance <= 0.3: 
                #충전소와 음식점의 거리 출력, 음식점 도로명주소 출력, 음식점 이름 출력
                print(f"Distance from Charger to Food: {food_distance:.2f} km")
                print(f"Food Location: {coords[2]}")
                print(f"restaurant name: {coords[3]}")
                print()