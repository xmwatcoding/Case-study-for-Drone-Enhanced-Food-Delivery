import xml.etree.ElementTree as ET
import pyproj
import math

# 定义6个指定的WGS84坐标点（lat, lng）
coordinates_wgs84 = [
    (22.5965,113.9623),
    (22.5948, 113.9723),
    (22.5914,113.9875),
    (22.5934,113.9948),
    (22.5964,113.9986),
    (22.5839, 113.9502)
]

def convert_coordinates(lng, lat):
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32649", always_xy=True)
    return transformer.transform(lng, lat)

def parse_network_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    nodes = {}
    for node in root.findall(".//node"):
        node_id = node.get("id")
        nodes[node_id] = (float(node.get("x")), float(node.get("y")))
    
    links = []
    for link in root.findall(".//link"):
        link_id = link.get("id")
        from_node = link.get("from")
        to_node = link.get("to")
        if from_node in nodes and to_node in nodes:
            links.append((link_id, nodes[from_node], nodes[to_node]))
    
    return links

def point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return math.dist((px, py), (x1, y1))
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx**2 + dy**2)))
    proj_x, proj_y = x1 + t * dx, y1 + t * dy
    return math.dist((px, py), (proj_x, proj_y))

def find_nearest_link(x, y, links):
    min_dist = float("inf")
    nearest_link = None
    for link_id, (x1, y1), (x2, y2) in links:
        dist = point_to_segment_distance(x, y, x1, y1, x2, y2)
        if dist < min_dist:
            min_dist = dist
            nearest_link = link_id
    return nearest_link

def create_stop_xml(stops, output_file):
    transit_schedule = ET.Element("transitSchedule")
    transit_stops = ET.SubElement(transit_schedule, "transitStops")

    for i, (x, y, link_ref_id) in enumerate(stops):
        ET.SubElement(
            transit_stops, "stopFacility",
            id=f"stop_{i}",
            x=str(x),
            y=str(y),
            linkRefId=link_ref_id,
            isBlocking="false"
        )

    tree = ET.ElementTree(transit_schedule)

    with open(output_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(b'<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v1.dtd">\n')
        tree.write(f, encoding="utf-8")

def main():
    network_file = "cropped_network.xml"
    output_file = "custom_stops.xml"

    print("Converting coordinates...")
    converted_coords = [convert_coordinates(lng, lat) for lat, lng in coordinates_wgs84]
    print(converted_coords)
    print("Parsing network...")
    links = parse_network_xml(network_file)

    print("Finding nearest links...")
    stops = [(x, y, find_nearest_link(x, y, links)) for x, y in converted_coords]

    print("Creating stop XML...")
    create_stop_xml(stops, output_file)
    print(f"{len(stops)} stops written to {output_file}")

if __name__ == "__main__":
    main()
