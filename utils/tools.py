import numpy as np
def polygons_to_xyxy(polygons):
    xyxys = []
    for polygon in polygons:
        xyxys.append([int(min(polygon[0],polygon[6])),int(min(polygon[1],polygon[3])),int(max(polygon[2],polygon[4])),int(max(polygon[5],polygon[7]))])
    return xyxys


def box1_cou_box2(box1, box2):
    '''
        contain? S_cross/S_box1
        cou = 1 means box1 in box2
    '''
    left_column_max = max(box1[0],box2[0])
    right_column_min = min(box1[2],box2[2])
    up_row_max = max(box1[1],box2[1])
    down_row_min = min(box1[3],box2[3])
    if left_column_max >= right_column_min or down_row_min <= up_row_max:
        return 0
    S_box1 = acc_area(box1)
    S_cross = (down_row_min - up_row_max) * (right_column_min - left_column_max)
    return S_cross / S_box1

def drop_boxs1_contain_in_boxs2(boxs1,boxs2,cou_threshold):
    '''
        去除boxs1中包含于boxs2中的box 返回boxs1需丢弃的索引
    '''
    drop_indexs = []
    for index,box1 in enumerate(boxs1):
        for box2 in boxs2:
            if box1_cou_box2(box1,box2) > cou_threshold:
                drop_indexs.append(index)
                break
    return drop_indexs

def merge_end_paragraph(boxs,merge_distance,merge_width):
    '''
        将段落最后的边界框按照设定阈值（大包小;距离小于距离阈值;位置在宽度阈值内）合并
    '''
    # 按照高度排序
    datas = boxs[np.argsort(boxs[:, 1])]
    # 获取存在大包小关系的待合并边框索引 list(list) 可能多个
    merge_indexs = []
    flags = [True for _ in range(len(datas))] # 用于标记是否已经进入待合并边框索引中
    for i in range(len(datas)): # 双重循环：可能有左右排列的边框
        # 是否已经待合并
        if not flags[i]: continue
        i_merge_indexs = [i]
        front = datas[i]
        for j in range(i+1,len(datas)):
            # 是否已经待合并
            if not flags[j]: continue
            # 满足待合并条件
            if acc_area(front) > acc_area(datas[j]) and datas[j][1] - front[3] < merge_distance and \
                    datas[j][0] > front[0] - merge_width and datas[j][2] < front[2] + merge_width:
                flags[j] = False
                i_merge_indexs.append(j)
                front = datas[j] # 以该边框继续往下搜
        if len(i_merge_indexs) > 1:
            flags[i] = False
            merge_indexs.append(i_merge_indexs)
    # 合并 没进入待合并列表的+待合并列表合并
    new_rects = [datas[i] for i in range(len(datas)) if flags[i]]
    for merge_index in merge_indexs:
        new_rects.append(connect_boxs([datas[i] for i in merge_index]))
    return new_rects

def acc_area(box):
    return (box[2]-box[0])*(box[3]-box[1])

def connect_boxs(boxs):
    boxs = np.array(boxs) # [box_num,4] -> (x1min,y1min,x2max,y2max)
    # 列反向最值
    x1min,y1min,_,_ = boxs.min(0)
    _,_,x2max,y2max = boxs.max(0)
    return np.array([x1min,y1min,x2max,y2max])

def xyxy_to_ncxcywh(box,w,h):
    x1, y1, x2, y2 = box
    dw = 1 / w
    dh = 1 / h
    ncx = (x1 + x2) / 2 * dw
    ncy = (y1 + y2) / 2 * dh
    nw = (x2 - x1) * dw
    nh = (y2 - y1) * dh
    return [ncx,ncy,nw,nh]

def drop_contain(boxs):
    drop_indexs = []
    for i in range(len(boxs)):
        for j in range(i+1,len(boxs)):
            if box1_contain_in_box2(boxs[j],boxs[i]):
                drop_indexs.append(j)
            if box1_contain_in_box2(boxs[i],boxs[j]):
                drop_indexs.append(i)
    return [boxs[i] for i in range(len(boxs)) if i not in drop_indexs]

def box1_contain_in_box2(box1,box2):
    if box2[0] <= box1[0] and box2[1] <= box1[1] and box2[2] >= box1[2] and box2[3] >= box1[3]:
        return True
    return False

# def cou(box1, box2):
#     '''
#         contain? S_cross/S_box1
#     '''
#     left_column_max = max(box1[0],box2[0])
#     right_column_min = min(box1[2],box2[2])
#     up_row_max = max(box1[1],box2[1])
#     down_row_min = min(box1[3],box2[3])
#     if left_column_max >= right_column_min or down_row_min <= up_row_max:
#         return 0
#     S_small = min(acc_area(box1),acc_area(box2))
#     S_cross = (down_row_min - up_row_max) * (right_column_min - left_column_max)
#     return S_cross / S_small
#
# def drop_contain(xyxys,confs,iou_threshold=0.9,conf_threshold=0.4):
#     drop_indexs = []
#     for i in range(len(xyxys)):
#         for j in range(i+1,len(xyxys)):
#             if cou(xyxys[i],xyxys[j]) >= iou_threshold: # 不存在包含关系
#                 continue
#             if acc_area(xyxys[i]) < acc_area(xyxys[j]) and confs[i] < conf_threshold: # 删除前者
#                 drop_indexs.append(i)
#             if acc_area(xyxys[j]) <= acc_area(xyxys[i]) and confs[j] < conf_threshold: # 删除后者
#                 drop_indexs.append(j)
#     return drop_indexs