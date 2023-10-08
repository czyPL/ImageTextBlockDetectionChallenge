# -*- coding: utf-8 -*-
import shutil
import gradio as gr
import argparse
import os
import cv2
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from paddleocr import PPStructure
from utils.BoxConnect import *
from utils.tools import *

def show_prev_img(curr_img_num):
    if curr_img_num == 0:
        return IMG_PATHS[curr_img_num], curr_img_num
    else:
        return IMG_PATHS[curr_img_num-1],curr_img_num-1

def show_after_img(curr_img_num):
    if curr_img_num == len(IMG_PATHS)-1:
        return IMG_PATHS[curr_img_num], curr_img_num
    else:
        return IMG_PATHS[curr_img_num+1],curr_img_num+1

def detect(img_path,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width):
    # TODO:表格检测与格内合并
    img = cv2.imread(img_path)  # BGR
    h, w, _ = img.shape

    # 行检测
    result = DBNet(img_path)
    rows_xyxys = polygons_to_xyxy(result['polygons']) if len(result['polygons']) != 0 else []
    if len(rows_xyxys) == 0:
        return img,rows_xyxys

    # 版面分析
    if layout_radio:
        result = Layout(img)
        layout_xyxys = []
        for r in result:
            if r['type'] not in ['text','title']:
                continue
            layout_xyxys.append(r['bbox'])
        # 根据版面分析结果与行检测结果合并
        drop_indexs = drop_boxs1_contain_in_boxs2(rows_xyxys,layout_xyxys,cou_threshold)
        rows_xyxys = [rows_xyxys[i] for i in range(len(rows_xyxys)) if i not in drop_indexs] + layout_xyxys

    # 行列合并
    new_rects = np.array(rows_xyxys)
    if row_threshold != 1:
        connector = BoxesConnector_row(new_rects, w, max_dist=row_dis, overlap_threshold=row_threshold)  # 行合并
        new_rects,_ = connector.connect_boxes()
    if col_threshold != 1:
        connector = BoxesConnector_col(new_rects, h, max_dist=col_dis, overlap_threshold=col_threshold)  # 列合并
        new_rects,_ = connector.connect_boxes()

    # 段落最后合并
    if merge_radio:
        new_rects = merge_end_paragraph(new_rects,merge_distance,merge_width)

    # # 剔除完全包含
    # new_rects = drop_contain(new_rects)

    return img,new_rects

def pseudo_annotation(img_path,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width):
    img,new_rects = detect(img_path,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width)
    for i,rect in enumerate(new_rects):
        cv2.rectangle(img,(rect[0], rect[1]), (rect[2], rect[3]),(0,0,255),5)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def save_annotation(curr_img_num,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width):
    # 存储image
    img_path = IMG_PATHS[curr_img_num]
    shutil.copy(img_path,os.path.join(SAVE_DIR,'images'))
    data_id = os.path.splitext(os.path.split(img_path)[-1])[0]
    img,new_rects = detect(img_path, layout_radio,cou_threshold,row_threshold, col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width)
    h, w, _ = img.shape
    output = []
    # 转yolo格式存储label
    for xyxy in new_rects:
        ncxcywh = xyxy_to_ncxcywh(xyxy, w, h)
        output.append("0 {} {} {} {}".format(ncxcywh[0], ncxcywh[1], ncxcywh[2], ncxcywh[3]))
    with open(os.path.join(SAVE_DIR,"labels", data_id + '.txt'), 'w') as f:
        f.write('\n'.join(output))
    raise gr.Error("保存成功！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_dir', default='./itbd_from_internet',type=str, help="img path prepare to label")
    parser.add_argument('--save_dir', default='./ITBD-999', type=str, help="where to save img and label")
    arg = parser.parse_args()

    # 创建存储目录
    if not os.path.exists(os.path.join(arg.save_dir,'images')):
        os.makedirs(os.path.join(arg.save_dir,'images'))
    if not os.path.exists(os.path.join(arg.save_dir,'labels')):
        os.makedirs(os.path.join(arg.save_dir,'labels'))
    SAVE_DIR = arg.save_dir

    # 获取待标注图像路径
    IMG_PATHS = [os.path.join(arg.img_dir,img_name) for img_name in os.listdir(arg.img_dir) if img_name.endswith('jpg') or img_name.endswith('png')]

    # DBNet
    DBNet = pipeline(Tasks.ocr_detection, model='damo/cv_resnet18_ocr-detection-db-line-level_damo')
    # PaddleOCR 版面分析
    Layout = PPStructure(table=False, ocr=False, show_log=False, layout_score_threshold=0.5, layout_nms_threshold=0.5)

    with gr.Blocks(title='ITBD标注') as ITBD:
        gr.Markdown("# <center>ITBD标注<center>")
        with gr.Column():
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(value=IMG_PATHS[0],label='待标注图片',type='filepath')
                    curr_img_num = gr.State(0) # 保存当前是哪张
                    with gr.Row():
                        button_left = gr.Button("← 上一张")
                        button_right = gr.Button("→ 下一张")
                    button_annotation = gr.Button("伪标注")
                with gr.Column():
                    image_output = gr.Image(label='伪标注结果',height=295)
                    button_save = gr.Button("保存伪标注")
            with gr.Row():
                with gr.Row():
                    layout_radio = gr.Radio(['否', '是'], value='否', type='index', label='版面分析?')
                    cou_threshold = gr.Slider(0, 1, 0.9, label='行与版面融合阈值', interactive=True)
                with gr.Row():
                    row_threshold = gr.Slider(0, 1, 1, label='行合并阈值', interactive=True)  # 1即不启用
                    row_dis = gr.Slider(0, 200, 15, label='行合并距离', interactive=True)
                with gr.Row():
                    col_threshold = gr.Slider(0, 1, 1, label='列合并阈值', interactive=True)
                    col_dis = gr.Slider(0, 200, 15, label='列合并距离', interactive=True)
                with gr.Row():
                    merge_radio = gr.Radio(['否', '是'], value='否', type='index', label='段落最后合并?')
                    merge_distance = gr.Slider(0, 100, 10, label='合并距离', interactive=True)
                    merge_width = gr.Slider(0, 50, 10, label='合并宽度', interactive=True)


        button_left.click(show_prev_img, inputs=curr_img_num, outputs=[image_input,curr_img_num])
        button_right.click(show_after_img, inputs=curr_img_num, outputs=[image_input,curr_img_num])
        button_annotation.click(pseudo_annotation,inputs=[image_input,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width], outputs=image_output)
        button_save.click(save_annotation,inputs=[curr_img_num,layout_radio,cou_threshold,row_threshold,col_threshold,row_dis,col_dis,merge_radio,merge_distance,merge_width])

    ITBD.launch(show_error=True, server_name="0.0.0.0", server_port=7860)
