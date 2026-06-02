import os
import wave
import csv
import glob
from datetime import datetime
import pyaudio
import speech_recognition as sr

class JarvisRecorder:
    # 문제 7: 음성 녹음 클래스 (PEP 8: CapWord)
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.output_folder = 'records'

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def record_audio(self, duration=5):
        audio = pyaudio.PyAudio()

        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print(f'{duration}초 동안 녹음을 시작합니다... (아무 말이나 해보세요!)')
        frames = []

        for _ in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)

        print('녹음이 완료되었습니다.')

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # 녹음된 데이터를 .wav 파일로 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'record_{timestamp}.wav'
        filepath = os.path.join(self.output_folder, filename)

        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            
        print(f'녹음 파일이 저장되었습니다: {filepath}')
        return filepath

    # [추가됨] 녹음된 오디오를 스피커로 재생하는 함수
    def play_audio(self, filepath):
        print('녹음된 음성을 스피커로 재생합니다... 🔊')
        with wave.open(filepath, 'rb') as wf:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True  # 스피커 출력 설정
            )
            
            data = wf.readframes(self.chunk)
            while data:
                stream.write(data)
                data = wf.readframes(self.chunk)
                
            stream.stop_stream()
            stream.close()
            audio.terminate()
        print('재생이 완료되었습니다.')


class JavisSttManager:
    # 수행과제: STT 변환 및 검색 클래스 (PEP 8: CapWord)
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def extract_text_and_save(self, audio_path):
        base_name = os.path.splitext(audio_path)[0]
        csv_path = f'{base_name}.csv'
        
        extracted_data = []
        chunk_duration = 10 
        current_time = 0
        
        try:
            with sr.AudioFile(audio_path) as source:
                while True:
                    try:
                        audio_chunk = self.recognizer.record(source, duration=chunk_duration)
                        if not audio_chunk.frame_data:
                            break
                        
                        text = self.recognizer.recognize_google(audio_chunk, language='ko-KR')
                        
                        minutes = current_time // 60
                        seconds = current_time % 60
                        time_str = f'{minutes:02d}:{seconds:02d}'
                        
                        extracted_data.append([time_str, text])
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        print('API 요청에 실패했습니다. 네트워크 상태를 확인하세요.')
                        break
                    except Exception:
                        break
                        
                    current_time += chunk_duration
        except Exception as e:
            print(f'파일을 읽는 중 오류가 발생했습니다: {e}')
            return

        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['time', 'text'])
            writer.writerows(extracted_data)
            
        print(f'{csv_path} 파일이 성공적으로 저장되었습니다.')

    def process_directory(self, directory_path):
        search_pattern = os.path.join(directory_path, '*.wav')
        audio_files = glob.glob(search_pattern)
        
        if not audio_files:
            print('지정된 경로에 처리할 오디오 파일이 없습니다.')
            return
            
        for file_path in audio_files:
            print(f'{file_path} 파일의 STT 변환을 시작합니다.')
            self.extract_text_and_save(file_path)

    def search_keyword_in_csv(self, keyword, directory_path):
        search_pattern = os.path.join(directory_path, '*.csv')
        csv_files = glob.glob(search_pattern)
        
        print(f"'{keyword}' 검색 결과입니다:")
        found = False
        
        for file_path in csv_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file)
                    next(reader) 
                    
                    for row in reader:
                        if len(row) >= 2:
                            time_str = row[0]
                            text = row[1]
                            
                            if keyword in text:
                                file_name = os.path.basename(file_path)
                                print(f'[{file_name}] {time_str} - {text}')
                                found = True
            except Exception:
                pass
                
        if not found:
            print('일치하는 내용이 없습니다.')


# ==========================================
# 실행 테스트 코드 (전체 시나리오 작동)
# ==========================================
if __name__ == '__main__':
    target_dir = 'records'
    
    # 1. 5초간 음성을 녹음하여 파일을 생성합니다.
    recorder = JarvisRecorder()
    saved_filepath = recorder.record_audio(duration=5)
    
    # 2. 방금 녹음된 파일을 스피커로 재생합니다.
    recorder.play_audio(saved_filepath)
    
    # 3. 방금 녹음된 파일을 불러와서 STT로 변환 후 CSV로 저장합니다.
    stt_manager = JavisSttManager()
    stt_manager.process_directory(target_dir)
    
    # 4. CSV 파일 안에서 특정 키워드를 검색합니다.
    search_word = '화성'
    stt_manager.search_keyword_in_csv(search_word, target_dir)
