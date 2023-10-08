import os
import cv2

def xyxy_to_ncxcywh(box,w,h):
    x1, y1, x2, y2 = box
    dw = 1 / w
    dh = 1 / h
    ncx = (x1 + x2) / 2 * dw
    ncy = (y1 + y2) / 2 * dh
    nw = (x2 - x1) * dw
    nh = (y2 - y1) * dh

    return [ncx,ncy,nw,nh]

img_path = './dataset/val/images'
label_old_path = './dataset/val/labels'
label_yolo_path = './ITBD_dataset/labels'

for gt_name in os.listdir(label_old_path):
    data_id = os.path.splitext(gt_name)[0]
    h, w, _ = cv2.imread(os.path.join(img_path,data_id+'.png')).shape
    gt_path = os.path.join(label_old_path,gt_name)
    with open(gt_path,'r') as f:
        strs = f.readlines()
    res = []
    for line in strs:
        xyxy = [int(i) for i in line.strip().split()[1:]] # xyxy
        ncxcywh = xyxy_to_ncxcywh(xyxy,w,h)
        res.append("0 {} {} {} {}".format(ncxcywh[0], ncxcywh[1], ncxcywh[2], ncxcywh[3]))
    res_str = "\n".join(res)
    with open(os.path.join(label_yolo_path,gt_name),'w') as f:
        f.write(res_str)


# import os
# res = []
# for i in os.listdir('./dataset/val/images'):
#     res.append("/workspace/yolov8/ITBD_dataset/images/{}".format(i))
# with open('train.txt', 'w') as f:
#     f.write('\n'.join(res))

