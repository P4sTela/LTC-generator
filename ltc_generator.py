#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LTC (Linear Timecode) Generator
-------------------------------
このスクリプトは、指定されたフレームレートとタイムコードでLTCを生成します。
生成されたLTCは音声ファイルとして保存されます。
"""

import numpy as np
import soundfile as sf
import argparse
from datetime import datetime
import struct

class LTCGenerator:
    def __init__(self, fps=60, sample_rate=48000, use_drop_frame=None, user_bits=None, user_bits_field=[0,0,0,0,0,0,0,0]):
        """
        LTCジェネレーターの初期化
        
        Parameters:
        -----------
        fps : int
            フレームレート（デフォルト: 60fps）
        sample_rate : int
            サンプルレート（デフォルト: 48000Hz）
        use_drop_frame : bool or None
            ドロップフレームフラグ（Noneの場合、29.97と59.94fpsでは自動的にTrue）
        user_bits_field : list
            ユーザービットフィールド（デフォルト: [0,0,0,0,0,0,0,0]）
        """
        self.fps = fps
        self.sample_rate = sample_rate
        self.bits_per_frame = 80  # LTCの1フレームあたりのビット数
        
        self.user_bits_field1 = user_bits_field[0]
        self.user_bits_field2 = user_bits_field[1]
        self.user_bits_field3 = user_bits_field[2]
        self.user_bits_field4 = user_bits_field[3]
        self.user_bits_field5 = user_bits_field[4]
        self.user_bits_field6 = user_bits_field[5]
        self.user_bits_field7 = user_bits_field[6]
        self.user_bits_field8 = user_bits_field[7]

    
    def _timecode_to_binary_for_60fps(self, hours, minutes, seconds, frames):
        """
        時間、分、秒、フレームをLTCのバイナリ形式に変換（60fps用）
        
        Parameters:
        -----------
        hours : int
            時間（0-23）
        minutes : int
            分（0-59）
        seconds : int
            秒（0-59）
        frames : int
            フレーム（0-59）
            
        Returns:
        --------
        list
            80ビットのLTCフレームを表すリスト（0または1）
        """
        if frames >= self.fps:
            raise ValueError(f"フレーム数は{self.fps-1}以下である必要があります")
            
        # 時間、分、秒、フレームをBCDエンコード
        frame_units = frames % 10
        frame_tens = frames // 10
        
        second_units = seconds % 10
        second_tens = seconds // 10
        
        minute_units = minutes % 10
        minute_tens = minutes // 10
        
        hour_units = hours % 10
        hour_tens = hours // 10
        
        # Frame number units(0-9)（00-03ビット）
        frame_bits = []
        for i in range(4):
            frame_bits.append(1 if (frame_units & (1 << i)) else 0)

        # User bits field 1(0-15)（04-07ビット）
        # フレーム番号が30以上の場合に1を設定
        frame_bits.append(1 if frames >= 30 else 0)
        frame_bits.append(0)
        frame_bits.append(0)
        frame_bits.append(0)
        
        # Frame number tens(0-5)（08-09ビット）
        # 10の位が1or4の時に1bit目が1、2or5の時に2bit目が1になるように設定
        frame_bits.append(1 if frame_tens in [1, 4] else 0)  # 1bit目
        frame_bits.append(1 if frame_tens in [2, 5] else 0)  # 2bit目

        # Drop frame flag(0-1)（10ビット）
        drop_frame_flag = 0  # ノンドロップフレーム

        # Color frame flag(0-1)（11ビット）
        color_frame_flag = 1
        frame_bits.extend([drop_frame_flag, color_frame_flag])

        # User bits field 2(0-15)（12-15ビット）
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 3)) else 0)
        
        # Seconds units(0-9)（16-19ビット）
        for i in range(4):  
            frame_bits.append(1 if (second_units & (1 << i)) else 0)

        # User bits field 3(0-15)（20-23ビット）
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 3)) else 0)

        # Seconds tens(0-5)（24-26ビット）
        frame_bits.append(1 if (second_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (second_tens & (1 << 1)) else 0)
        frame_bits.append(1 if (second_tens & (1 << 2)) else 0)

        # Polarity correction bit(0-1)（27ビット）
        phase_correction_bit = 0
        frame_bits.append(phase_correction_bit)

        # User bits field 4(0-15)（28-31ビット）
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 3)) else 0)
        
        # Minutes units(0-9)（32-35ビット）
        for i in range(4):
            frame_bits.append(1 if (minute_units & (1 << i)) else 0)

        # User bits field 5(0-15)（36-39ビット）
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 3)) else 0)

        # Minutes tens(0-5)（40-42ビット）
        frame_bits.append(1 if (minute_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (minute_tens & (1 << 1)) else 0)
        frame_bits.append(1 if (minute_tens & (1 << 2)) else 0)
        
        # Binary group flag (43ビット)
        binary_group_flag = 0
        frame_bits.append(binary_group_flag)

        # User bits field 6(0-15)（44-47ビット）
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 3)) else 0)
        
        # Hours units(0-9)（48-51ビット）
        for i in range(4):
            frame_bits.append(1 if (hour_units & (1 << i)) else 0)

        # User bits field 7(0-15)（52-55ビット）
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 3)) else 0)
        
        # Hours tens(0-2)（56-57ビット）
        frame_bits.append(1 if (hour_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (hour_tens & (1 << 1)) else 0)

        # Clock flag (58ビット)
        clock_flag = 0
        frame_bits.append(clock_flag)

        # Binary group flag (59ビット)
        binary_group_flag = 0
        frame_bits.append(binary_group_flag)

        # User bits field 8(0-15)（60-63ビット）
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 3)) else 0)

        # Sync word(64-79ビット)
        frame_bits.extend([0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1])

        # フレームビットの合計を計算し、偶数パリティを確保
        parity_sum = sum(frame_bits)
        if parity_sum % 2 == 1:  # 奇数の場合
            frame_bits[27] = 1  # Polarity correction bitを1に設定
        
        return frame_bits
    
    def _timecode_to_binary(self, hours, minutes, seconds, frames):
        """
        時間、分、秒、フレームをLTCのバイナリ形式に変換
        
        Parameters:
        -----------
        hours : int
            時間（0-23）
        minutes : int
            分（0-59）
        seconds : int
            秒（0-59）
        frames : int
            フレーム（0-fps-1）
            
        Returns:
        --------
        list
            80ビットのLTCフレームを表すリスト（0または1）
        """
        if frames >= self.fps:
            raise ValueError(f"フレーム数は{self.fps-1}以下である必要があります")
            
        # 時間、分、秒、フレームをBCDエンコード
        frame_units = frames % 10
        frame_tens = frames // 10
        
        second_units = seconds % 10
        second_tens = seconds // 10
        
        minute_units = minutes % 10
        minute_tens = minutes // 10
        
        hour_units = hours % 10
        hour_tens = hours // 10
        
        # Frame number units(0-9)（00-03ビット）
        frame_bits = []
        for i in range(4):
            frame_bits.append(1 if (frame_units & (1 << i)) else 0)

        # User bits field 1(0-15)（04-07ビット）
        frame_bits.append(1 if (self.user_bits_field1 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field1 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field1 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field1 & (1 << 3)) else 0)
        
        # Frame number tens(0-2)（08-09ビット）
        frame_bits.append(1 if (frame_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (frame_tens & (1 << 1)) else 0)

        # Drop frame flag(0-1)（10ビット）
        drop_frame_flag = 0  # ノンドロップフレーム

        # Color frame flag(0-1)（11ビット）
        color_frame_flag = 1
        frame_bits.extend([drop_frame_flag, color_frame_flag])

        # User bits field 2(0-15)（12-15ビット）
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field2 & (1 << 3)) else 0)
        
        # Seconds units(0-9)（16-19ビット）
        for i in range(4):  
            frame_bits.append(1 if (second_units & (1 << i)) else 0)

        # User bits field 3(0-15)（20-23ビット）
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field3 & (1 << 3)) else 0)

        # Seconds tens(0-5)（24-26ビット）
        frame_bits.append(1 if (second_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (second_tens & (1 << 1)) else 0)
        frame_bits.append(1 if (second_tens & (1 << 2)) else 0)

        # Polarity correction bit(0-1)（27ビット）
        phase_correction_bit = 0
        frame_bits.append(phase_correction_bit)

        # User bits field 4(0-15)（28-31ビット）
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field4 & (1 << 3)) else 0)
        
        # Minutes units(0-9)（32-35ビット）
        for i in range(4):
            frame_bits.append(1 if (minute_units & (1 << i)) else 0)

        # User bits field 5(0-15)（36-39ビット）
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field5 & (1 << 3)) else 0)

        # Minutes tens(0-5)（40-42ビット）
        frame_bits.append(1 if (minute_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (minute_tens & (1 << 1)) else 0)
        frame_bits.append(1 if (minute_tens & (1 << 2)) else 0)
        
        # Binary group flag (43ビット)
        binary_group_flag = 0
        frame_bits.append(binary_group_flag)

        # User bits field 6(0-15)（44-47ビット）
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field6 & (1 << 3)) else 0)
        
        # Hours units(0-9)（48-51ビット）
        for i in range(4):
            frame_bits.append(1 if (hour_units & (1 << i)) else 0)

        # User bits field 7(0-15)（52-55ビット）
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field7 & (1 << 3)) else 0)
        
        # Hours tens(0-2)（56-57ビット）
        frame_bits.append(1 if (hour_tens & (1 << 0)) else 0)
        frame_bits.append(1 if (hour_tens & (1 << 1)) else 0)

        # Clock flag (58ビット)
        clock_flag = 0
        frame_bits.append(clock_flag)

        # Binary group flag (59ビット)
        binary_group_flag = 0
        frame_bits.append(binary_group_flag)

        # User bits field 8(0-15)（60-63ビット）
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 0)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 1)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 2)) else 0)
        frame_bits.append(1 if (self.user_bits_field8 & (1 << 3)) else 0)

        # Sync word(64-79ビット)
        frame_bits.extend([0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,1])

        # フレームビットの合計を計算し、偶数パリティを確保
        parity_sum = sum(frame_bits)
        if parity_sum % 2 == 1:  # 奇数の場合
            frame_bits[27] = 1  # Polarity correction bitを1に設定
        
        return frame_bits
    
    def _generate_ltc_waveform(self, ltc_bits):
        """
        LTCビットからオーディオ波形を生成
        
        Parameters:
        -----------
        ltc_bits : list
            80ビットのLTCフレームを表すリスト
            
        Returns:
        --------
        numpy.ndarray
            LTC波形を表す配列
        """
        # 1ビットあたりのサンプル数を計算
        samples_per_bit = int(self.sample_rate / (self.fps * self.bits_per_frame))
        # 1ビットの半分のサンプル数
        half_samples_per_bit = samples_per_bit // 2
        
        # 波形を生成
        waveform = []
        current_level = 1  # 初期レベル
        
        for bit in ltc_bits:
            # 最初の半分のサンプル
            waveform.extend([current_level] * half_samples_per_bit)
            
            if bit == 1:
                # ビットの中間でレベルを反転
                current_level = -current_level
            
            # 後半の半分のサンプル
            waveform.extend([current_level] * half_samples_per_bit)
            
            current_level = -current_level
            
        return np.array(waveform, dtype=np.float32)
    
    def generate_ltc(self, hours, minutes, seconds, frames, duration=1.0):
        """
        指定された時間、分、秒、フレームでLTCを生成
        
        Parameters:
        -----------
        hours : int
            時間（0-23）
        minutes : int
            分（0-59）
        seconds : int
            秒（0-59）
        frames : int
            フレーム（0-fps-1）
        duration : float
            生成するLTCの長さ（秒）
            
        Returns:
        --------
        numpy.ndarray
            LTC波形を表す配列
        """
        # 生成するフレーム数を計算
        num_frames = int(duration * self.fps)
        
        # 波形を格納する配列
        waveform = np.array([], dtype=np.float32)
        
        # 指定された数のフレームを生成
        for i in range(num_frames):
            # 現在のタイムコードを計算
            current_frames = (frames + i) % self.fps
            current_seconds = (seconds + (frames + i) // self.fps) % 60
            current_minutes = (minutes + (seconds + (frames + i) // self.fps) // 60) % 60
            current_hours = (hours + (minutes + (seconds + (frames + i) // self.fps) // 60) // 60) % 24
            
            # LTCビットを生成
            if self.fps == 60:
                ltc_bits = self._timecode_to_binary_for_60fps(current_hours, current_minutes, current_seconds, current_frames)
            else:
                ltc_bits = self._timecode_to_binary(current_hours, current_minutes, current_seconds, current_frames)
            
            # 波形を生成して追加
            frame_waveform = self._generate_ltc_waveform(ltc_bits)
            waveform = np.append(waveform, frame_waveform)
        
        return waveform
    
    def save_to_file(self, waveform, filename):
        """
        波形をオーディオファイルとして保存
        
        Parameters:
        -----------
        waveform : numpy.ndarray
            保存する波形
        filename : str
            出力ファイル名
        """
        sf.write(filename, waveform, self.sample_rate)
        print(f"LTCを {filename} に保存しました")

def main():
    parser = argparse.ArgumentParser(description='SMPTE LTC (Linear Timecode) Generator')
    parser.add_argument('--fps', type=int, default=60, help='フレームレート（デフォルト: 60fps）')
    parser.add_argument('--sample-rate', type=int, default=48000, help='サンプルレート（デフォルト: 48000Hz）')
    parser.add_argument('--hours', type=int, default=0, help='時間（0-23）')
    parser.add_argument('--minutes', type=int, default=0, help='分（0-59）')
    parser.add_argument('--seconds', type=int, default=0, help='秒（0-59）')
    parser.add_argument('--frames', type=int, default=0, help='フレーム（0-fps-1）')
    parser.add_argument('--duration', type=float, default=5.0, help='生成するLTCの長さ（秒）')
    parser.add_argument('--output', type=str, default='ltc_output.wav', help='出力ファイル名')
    parser.add_argument('--current-time', action='store_true', help='現在の時刻を使用')
    
    # ユーザービット関連の引数を追加
    parser.add_argument('--user-bits-field1', type=int, default=0, help='ユーザービットフィールド1（4ビット: 0-15）')
    parser.add_argument('--user-bits-field2', type=int, default=0, help='ユーザービットフィールド2（4ビット: 0-15）')
    parser.add_argument('--user-bits-field3', type=int, default=0, help='ユーザービットフィールド3（4ビット: 0-15）')
    parser.add_argument('--user-bits-field4', type=int, default=0, help='ユーザービットフィールド4（4ビット: 0-15）')
    parser.add_argument('--user-bits-field5', type=int, default=0, help='ユーザービットフィールド5（4ビット: 0-15）')
    parser.add_argument('--user-bits-field6', type=int, default=0, help='ユーザービットフィールド6（4ビット: 0-15）')
    parser.add_argument('--user-bits-field7', type=int, default=0, help='ユーザービットフィールド7（4ビット: 0-15）')
    parser.add_argument('--user-bits-field8', type=int, default=0, help='ユーザービットフィールド8（4ビット: 0-15）')
    
    args = parser.parse_args()
    
    # LTCジェネレーターを初期化
    ltc_gen = LTCGenerator(
        fps=args.fps,
        sample_rate=args.sample_rate,
        user_bits_field=[args.user_bits_field1, args.user_bits_field2, args.user_bits_field3, args.user_bits_field4, args.user_bits_field5, args.user_bits_field6, args.user_bits_field7, args.user_bits_field8]
    )
    
    # 現在の時刻を使用する場合
    if args.current_time:
        now = datetime.now()
        hours = now.hour
        minutes = now.minute
        seconds = now.second
        frames = int((now.microsecond / 1000000) * args.fps)
    else:
        hours = args.hours
        minutes = args.minutes
        seconds = args.seconds
        frames = args.frames
    
    # LTCを生成
    waveform = ltc_gen.generate_ltc(hours, minutes, seconds, frames, args.duration)
    
    # ファイルに保存
    ltc_gen.save_to_file(waveform, args.output)

if __name__ == "__main__":
    main() 