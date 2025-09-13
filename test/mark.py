import sys
import os
import cv2
import numpy as np

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from image_processing.line_processing import ImageLineProcessing, ColorLine


def main(input_dir=".", start=1, end=150, marked_file="marked.txt"):
    height = 480
    width = 640

    index = start
    marked = set()

    while True:
        filename = f"{index}.png"
        filepath = os.path.join(input_dir, filename)

        if not os.path.exists(filepath):
            print(f"Файл {filepath} не найден")
            key = cv2.waitKey(0) & 0xFF
            if key == ord('d'):  # вперед
                index = min(end, index + 1)
                continue
            elif key == ord('a'):  # назад
                index = max(start, index - 1)
                continue
            elif key == ord('q'):  # выход
                break
            else:
                continue

        img = cv2.imread(filepath)

        # обработка
        yellow = ImageLineProcessing(img.copy(), width, height, ColorLine.yellow)
        yellow_angle = yellow.process()

        white = ImageLineProcessing(img.copy(), width, height, ColorLine.white)
        white_angle = white.process()

        # итоговое изображение (наложим оба результата)
        yellow_outfile = os.path.join('.', f"lineColorLine.yellow.png")
        white_outfile = os.path.join('.', f"lineColorLine.white.png")
        yellow_img = cv2.imread(yellow_outfile)
        white_img = cv2.imread(white_outfile)
        combined = cv2.addWeighted(yellow_img, 0.5,white_img, 0.5, 0)

        cv2.imshow("Result", combined)
        print(f"[{index}] yellow={yellow_angle:.2f}, white={white_angle:.2f}")

        key = cv2.waitKey(0) & 0xFF

        if key == ord('d'):  # вперед
            index = min(end, index + 1)
        elif key == ord('a'):  # назад
            index = max(start, index - 1)
        elif key == ord('m'):  # отметить
            marked.add(index)
            print(f"Добавлен {index} в список")
            with open(marked_file, "w") as f:
                f.write("\n".join(map(str, sorted(marked))))
        elif key == ord('q'):  # выход
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(input_dir=".", start=1, end=150)
