"""Small synthetic checks; no dataset credentials needed."""
import argparse
import importlib.metadata
import platform
import tempfile
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--official', action='store_true')
    args = parser.parse_args()
    print(f'Python {platform.python_version()} / {platform.system()}')
    for package in ('numpy', 'matplotlib', 'pandas', 'jupyterlab'):
        print(f'{package}: {importlib.metadata.version(package)}')
    timestamps = np.arange(1, 21) / 4
    trajectory = np.column_stack((timestamps * 2, np.zeros(20)))
    assert trajectory.shape == (20, 2)
    assert timestamps[0] == 0.25 and timestamps[-1] == 5.0
    if not args.official:
        print('PASS: basic preparation environment. Official Waymo ops NOT tested.')
        return
    import tensorflow as tf
    import cv2
    from waymo_open_dataset.protos import end_to_end_driving_data_pb2 as data_pb2
    from waymo_open_dataset.protos import end_to_end_driving_submission_pb2 as submission_pb2
    from waymo_open_dataset.wdl_limited.camera.ops import py_camera_model_ops

    frame = data_pb2.E2EDFrame()
    frame.frame.context.name = 'synthetic-smoke-test'
    with tempfile.TemporaryDirectory() as temp:
        path = str(Path(temp) / 'sample.tfrecord')
        with tf.io.TFRecordWriter(path) as writer:
            writer.write(frame.SerializeToString())
        restored = data_pb2.E2EDFrame()
        restored.ParseFromString(next(iter(tf.data.TFRecordDataset([path]))).numpy())
        assert restored == frame
    prediction = submission_pb2.TrajectoryPrediction(
        pos_x=trajectory[:, 0], pos_y=trajectory[:, 1])
    submission = submission_pb2.E2EDChallengeSubmission(predictions=[
        submission_pb2.FrameTrajectoryPredictions(
            frame_name=frame.frame.context.name, trajectory=prediction)])
    restored_submission = submission_pb2.E2EDChallengeSubmission()
    restored_submission.ParseFromString(submission.SerializeToString())
    assert restored_submission == submission
    print(f'TensorFlow {tf.__version__}; OpenCV {cv2.__version__}')
    print(f'GPUs: {tf.config.list_physical_devices("GPU")}')
    print('PASS: TFRecord / E2EDFrame / submission round trip; camera ops imported.')


if __name__ == '__main__':
    main()
