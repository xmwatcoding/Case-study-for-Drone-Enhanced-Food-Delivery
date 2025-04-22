import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import DBSCAN
import networkx as nx

def process_network(input_file, output_file, eps=1.0):
    # 解析XML文件
    tree = ET.parse(input_file)
    root = tree.getroot()

    # 解析节点
    nodes = {}
    for node in root.findall('./nodes/node'):
        node_id = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        nodes[node_id] = (x, y)

    # 解析链接
    links = []
    for link in root.findall('./links/link'):
        link_data = {
            'id': link.get('id'),
            'from': link.get('from'),
            'to': link.get('to'),
            'length': link.get('length'),
            'freespeed': link.get('freespeed'),
            'capacity': link.get('capacity'),
            'permlanes': link.get('permlanes'),
            'oneway': link.get('oneway'),
            'modes': link.get('modes'),
            'attributes': {}
        }
        # 解析属性
        attributes = link.find('./attributes')
        if attributes is not None:
            for attr in attributes.findall('attribute'):
                name = attr.get('name')
                cls = attr.get('class')
                value = attr.text
                link_data['attributes'][name] = {'class': cls, 'value': value}
        links.append(link_data)

    # 节点聚类合并
    coords = np.array([(x, y) for x, y in nodes.values()])
    db = DBSCAN(eps=eps, min_samples=1).fit(coords)
    labels = db.labels_

    # 创建新节点集合
    new_nodes = {}
    node_map = {}
    for idx, (node_id, (x, y)) in enumerate(nodes.items()):
        label = labels[idx]
        if label not in new_nodes:
            # 创建新节点ID并计算平均坐标
            new_id = f"c{label}"
            cluster_points = coords[labels == label]
            avg_x = np.mean(cluster_points[:, 0])
            avg_y = np.mean(cluster_points[:, 1])
            new_nodes[new_id] = (avg_x, avg_y)
        node_map[node_id] = new_id

    # 处理链接
    valid_links = []
    for link in links:
        try:
            from_node = node_map[link['from']]
            to_node = node_map[link['to']]
            
            # 跳过自环链接
            if from_node == to_node:
                continue
                
            # 计算新长度
            x1, y1 = new_nodes[from_node]
            x2, y2 = new_nodes[to_node]
            new_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            # 创建新链接
            new_link = {
                'from': from_node,
                'to': to_node,
                'length': new_length,
                'id': link['id'],
                'freespeed': link['freespeed'],
                'capacity': link['capacity'],
                'permlanes': link['permlanes'],
                'oneway': link['oneway'],
                'modes': link['modes'],
                'attributes': link['attributes']
            }
            valid_links.append(new_link)
        except KeyError:
            continue

    # 去重链接
    unique_links = {}
    for link in valid_links:
        key = (link['from'], link['to'])
        if key not in unique_links:
            unique_links[key] = link
    dedup_links = list(unique_links.values())

    # 构建网络图
    G = nx.DiGraph()
    G.add_nodes_from(new_nodes.keys())
    for link in dedup_links:
        G.add_edge(link['from'], link['to'])

    # 获取最大连通组件
    scc = list(nx.strongly_connected_components(G))
    largest = max(scc, key=len)
    valid_nodes = largest

    # 过滤节点和链接
    final_nodes = {n: new_nodes[n] for n in valid_nodes}
    final_links = [link for link in dedup_links 
                  if link['from'] in valid_nodes and link['to'] in valid_nodes]

    # 创建新的XML结构
    new_root = ET.Element('network')
    
    # 添加坐标系属性
    attr_elem = ET.SubElement(new_root, 'attributes')
    crs = ET.SubElement(attr_elem, 'attribute', 
                       {'name': 'coordinateReferenceSystem', 'class': 'java.lang.String'})
    crs.text = root.find('.//attribute[@name="coordinateReferenceSystem"]').text

    # 添加处理后的节点
    nodes_elem = ET.SubElement(new_root, 'nodes')
    for nid, (x, y) in final_nodes.items():
        ET.SubElement(nodes_elem, 'node', {'id': nid, 'x': str(x), 'y': str(y)})

    # 添加处理后的链接
    links_elem = ET.SubElement(new_root, 'links', {
        'capperiod': root.find('./links').get('capperiod'),
        'effectivecellsize': root.find('./links').get('effectivecellsize'),
        'effectivelanewidth': root.find('./links').get('effectivelanewidth')
    })
    
    for link in final_links:
        link_elem = ET.SubElement(links_elem, 'link', {
            'id': link['id'],
            'from': link['from'],
            'to': link['to'],
            'length': str(link['length']),
            'freespeed': link['freespeed'],
            'capacity': link['capacity'],
            'permlanes': link['permlanes'],
            'oneway': link['oneway'],
            'modes': link['modes']
        })
        
        # 添加额外属性
        if link['attributes']:
            attr_elem = ET.SubElement(link_elem, 'attributes')
            for name, data in link['attributes'].items():
                ET.SubElement(attr_elem, 'attribute', 
                            {'name': name, 'class': data['class']}).text = data['value']

    # 保存新文件
    tree = ET.ElementTree(new_root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    process_network('cropped_network.xml', 'processed_network.xml', eps=1.0)