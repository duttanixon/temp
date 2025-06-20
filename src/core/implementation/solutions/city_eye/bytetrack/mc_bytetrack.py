#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from .tracker.byte_tracker import BYTETracker


class dict_dot_notation(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class MultiClassByteTrack(object):
    def __init__(
        self,
        fps,
        track_thresh=0.5,
        track_buffer=5,
        match_thresh=0.8,
        min_box_area=10,
        mot20=False,
    ):
        self.min_box_area = min_box_area

        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.mot20 = mot20
        self.fps = fps
        self.class_ids=[1,2,3,4,6,8]

        # ByteTracker保持用Dict生成
        self.tracker_dict = {}

    def __call__(
        self,
        image,
        bboxes,
        scores,
        class_ids,
    ):
        # vehicle_class_ids = [2, 5, 7]  # Example: car, truck, bus
        original_class_ids = np.array(class_ids)
        # Convert all vehicle class ids to a single class id
        # class_ids = np.where(np.isin(class_ids, vehicle_class_ids), 2, class_ids)
        # unique_class_ids = np.unique(class_ids)
        for class_id in original_class_ids:
            class_id = int(class_id)
            if class_id not in self.class_ids:
                continue
            if class_id not in self.tracker_dict:
                self.tracker_dict[class_id] = BYTETracker(
                    args=dict_dot_notation(
                        {
                            "track_thresh": self.track_thresh,
                            "track_buffer": self.track_buffer,
                            "match_thresh": self.match_thresh,
                            "mot20": self.mot20,
                        }
                    ),
                    frame_rate=self.fps,
                )

        t_ids, t_bboxes, t_scores, t_class_ids = [], [], [], []

        for class_id in self.tracker_dict.keys():
            # 対象クラス抽出
            # target_index = np.in1d(class_ids, np.array(int(class_id)))
            target_index = np.where(class_ids == class_id)[0]

            if len(target_index) == 0:
                continue

            # target_bboxes = np.array(bboxes)[target_index]
            # target_scores = np.array(scores)[target_index]
            target_class_ids = np.array(class_ids)[target_index]
            target_bboxes1 = bboxes[target_index]
            target_scores1 = scores[target_index]

            # トラッカー用変数に格納
            # detections = [[*b, s, l] for b, s, l in zip(
            #     target_bboxes, target_scores, target_class_ids)]
            # detections = np.array(detections)
            detections = np.hstack(
                (
                    target_bboxes1,
                    target_scores1[:, np.newaxis],
                    target_class_ids[:, np.newaxis],
                )
            )

            # トラッカー更新
            result = self._tracker_update(
                self.tracker_dict[class_id],
                image,
                detections,
            )

            # 結果格納
            for bbox, score, t_id in zip(result[0], result[1], result[2]):
                t_ids.append(f"{class_id}_{t_id}")
                t_bboxes.append(bbox)
                t_scores.append(score)
                # t_class_ids.append(class_id)
                original_class_id = original_class_ids[
                    target_index[np.where(result[0] == bbox)[0][0]]
                ]
                t_class_ids.append(original_class_id)

        return t_ids, t_bboxes, t_scores, t_class_ids

    def _tracker_update(self, tracker, image, detections):
        image_info = {
            "id": 0,
            "image": image,
            "width": image.shape[1],
            "height": image.shape[0],
        }

        online_targets = []
        if detections.size > 0:
            online_targets = tracker.update(
                detections[:, :-1],
                [image_info["height"], image_info["width"]],
                [image_info["height"], image_info["width"]],
            )

        online_tlwhs, online_ids, online_scores = [], [], []
        for online_target in online_targets:
            tlwh = online_target.tlwh
            if tlwh[2] * tlwh[3] > self.min_box_area:
                online_tlwhs.append(
                    np.array([tlwh[0], tlwh[1], tlwh[0] + tlwh[2], tlwh[1] + tlwh[3]])
                )
                online_ids.append(online_target.track_id)
                online_scores.append(online_target.score)
            # else:
            #     print(f'area is too small: {tlwh[2] * tlwh[3]}')

        return online_tlwhs, online_scores, online_ids

    # def _tracker_update(self, tracker, image, detections):
    #     image_info = {'id': 0}
    #     image_info['image'] = copy.deepcopy(image)
    #     image_info['width'] = image.shape[1]
    #     image_info['height'] = image.shape[0]
    #
    #     online_targets = []
    #     if detections is not None and len(detections) != 0:
    #         online_targets = tracker.update(
    #             detections[:, :-1],
    #             [image_info['height'], image_info['width']],
    #             [image_info['height'], image_info['width']],
    #         )
    #
    #     online_tlwhs = []
    #     online_ids = []
    #     online_scores = []
    #     for online_target in online_targets:
    #         tlwh = online_target.tlwh
    #         track_id = online_target.track_id
    #         if tlwh[2] * tlwh[3] > self.min_box_area:
    #             online_tlwhs.append(
    #                 np.array([
    #                     tlwh[0], tlwh[1], tlwh[0] + tlwh[2], tlwh[1] + tlwh[3]
    #                 ]))
    #             online_ids.append(track_id)
    #             online_scores.append(online_target.score)
    #
    #     return online_tlwhs, online_scores, online_ids
