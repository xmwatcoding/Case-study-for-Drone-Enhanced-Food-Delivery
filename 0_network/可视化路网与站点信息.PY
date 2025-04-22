import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def parse_network(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    nodes = {}
    links = []

    for node in root.findall(".//node"):
        node_id = node.get("id")
        x = float(node.get("x"))
        y = float(node.get("y"))
        nodes[node_id] = (x, y)
    
    for link in root.findall(".//link"):
        from_node = link.get("from")
        to_node = link.get("to")
        if from_node in nodes and to_node in nodes:
            x1, y1 = nodes[from_node]
            x2, y2 = nodes[to_node]
            links.append(((x1, y1), (x2, y2)))
    
    return nodes, links

def parse_stops(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    stops = []

    for stop in root.findall(".//stopFacility"):
        stop_id = stop.get("id")
        x = float(stop.get("x"))
        y = float(stop.get("y"))
        stops.append((stop_id, x, y))
    
    return stops

def plot_network_and_stops(network_file, stops_file):
    print("Parsing network...")
    nodes, links = parse_network(network_file)

    print("Parsing stops...")
    stops = parse_stops(stops_file)

    print("Plotting...")
    fig, ax = plt.subplots(figsize=(10, 10))

    # 绘制路网连线
    for (x1, y1), (x2, y2) in links:
        ax.plot([x1, x2], [y1, y2], color='gray', linewidth=1)

    # 绘制 stop 点
    for stop_id, x, y in stops:
        if stop_id == "stop_5":
            ax.plot(x, y, 'ro', label="Take-off Point", markersize=5)  # 红色
        elif stop_id == "stop_4":
            ax.plot(x, y, 'bo', label="Drop-off Point", markersize=5)  # 蓝色
        else:
            ax.plot(x, y, 'bo', markersize=5)  # 蓝色

    # 图例和美化
    ax.set_title("Network and Delivery Stops", fontsize=14)
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.set_aspect("equal")
    ax.legend()
    plt.grid(False)
    plt.tight_layout()
    plt.show()

# 使用示例（替换为你的实际文件名）
plot_network_and_stops("cropped_network.xml", "custom_stops.xml")
