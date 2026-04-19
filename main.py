#!/usr/bin/env python3

import pygame
import numpy as np
import matplotlib.pyplot as plt
import colorsys
import wave

import time

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)

D_WIDTH, D_HEIGHT = 1850, 800
display = pygame.display.set_mode((D_WIDTH, D_HEIGHT))

#audiofilename = 'file2amono.wav'
audiofilename = 'untitleda.wav'
with open(audiofilename, 'rb') as f:
    raw_data = f.read()
    hexadecimal_string_data = [hex(n)[2:].zfill(2) for n in raw_data]

with wave.open(audiofilename, 'rb') as wavefile:
    sample_rate = wavefile.getparams().framerate

print()
print(f'Loading file: {audiofilename}')
print(f'Sample rate: {sample_rate} hz')
print()

seconds_to_load = 2
hzr = sample_rate
hz = sample_rate*seconds_to_load
d = hexadecimal_string_data[80:80+hz*2]

tmp = []
alls = []
for i in range(len(d)):
    tmp.append(str(d[i]))
    if (i - 1) % 2 == 0:
        strf = ''.join(tmp)
        signed_int = int.from_bytes(bytes.fromhex(
            strf), byteorder='little', signed=True)
        alls.append(signed_int)
        tmp = []


def main():
    width = D_WIDTH / hz
    baseline = D_HEIGHT/8

    index = 0
    index_change = 0
    width_change = 0

    pygame.font.init()
    font = pygame.font.SysFont('Consolas', 15)

    onesurf = font.render('1', False, WHITE)
    twosurf = font.render('2', False, WHITE)
    threesurf = font.render('3', False, WHITE)

    def get_freqs_and_amplitudes(hzrrange0, hzrrange1):
        firstsplice = alls[int(hzr*hzrrange0):int(hzr*hzrrange1)]

        X = np.fft.fft(firstsplice)
        sample_amt = len(X)
        n = np.arange(sample_amt)
        T = sample_amt/hzr
        freq = n/T
        freqq = np.delete(freq, 0)

        XX = np.delete(X, 0)
        XXX = np.abs(XX)

        XXXX = np.array_split(XXX, 2)[0]
        freqqq = np.array_split(freqq, 2)[0]

        print(freqqq)
        return freqqq, XXXX

    starting_time = 0.01
    hzrrange0 = starting_time
    interval = 0.005
    freq_n = len(get_freqs_and_amplitudes(hzrrange0, hzrrange0+interval)[0])
    ALL = []
    maxs = []

    A = time.time()
    for _ in range(int((seconds_to_load - hzrrange0)*(1/interval))):
        this = list(get_freqs_and_amplitudes(hzrrange0, hzrrange0+interval))
        maxs.append(max(this[1]))
        ALL.append(this)
        try:
            assert freq_n == len(ALL[-1][0])
        except AssertionError:
            # insert a 0 value at the highest frequency.
            ALL[-1][0] = np.append(ALL[-1][0], [[ALL[-1][0][-1]]])
            ALL[-1][1] = np.append(ALL[-1][1], [[0]])
        hzrrange0 += interval
    assert all(len(ALL[i][0]) for i, _ in enumerate(ALL))
    B = time.time()
    print(f'FFT time: {B - A} seconds')

    pygame.mixer.init()
    pygame.mixer.music.load(audiofilename)
    playing = False

    seconds_in = 0
    clock = pygame.time.Clock()
    frames = 0

    selected = 0
    while True:
        display.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    index_change = 5
                if event.key == pygame.K_a:
                    index_change = -5
                if event.key == pygame.K_UP:
                    width_change = 0.001
                if event.key == pygame.K_DOWN:
                    width_change = -0.001
                if event.key == pygame.K_SPACE:
                    playing = not playing
                    if playing:
                        pygame.mixer.music.play()
                        seconds_in = 0
                    else:
                        pygame.mixer.music.stop()
                if event.key == pygame.K_RIGHT:
                    selected += 1
                if event.key == pygame.K_LEFT:
                    selected -= 1
            if event.type == pygame.KEYUP:
                index_change = 0
                width_change = 0

        clock.tick()
        frames += 1
        fps = clock.get_fps()

        if playing:
            seconds_in += (1 / fps)

        index += index_change
        width += width_change

        # Display spectrogram
        for i, elem in enumerate(ALL):
            freqs = elem[0]
            ampss = elem[1]
            max_amps = max(maxs)

            gap = 1
            height = (D_HEIGHT - 200) / len(ALL[0][0])
            print(height)

            for j, (freq, amps) in enumerate(zip(freqs, ampss)):
                ratio = amps/max_amps
                hsv = colorsys.hsv_to_rgb(ratio, 0.9, 0.6*ratio+0.3)
                color = hsv[0] * 255, hsv[1] * 255, hsv[2] * 255

                rect = (
                    ((starting_time+interval*i)*width*hzr),
                    750 - j * (height+gap),  # y
                    interval*width*hzr,
                    height,)

                pygame.draw.rect(display, color, rect)

        # Draw selector
        pygame.draw.rect(display, WHITE, ((starting_time + interval*selected)*width*hzr,
                                          750 + 10,
                                          interval*width*hzr,
                                          200))

        # print(ALL[selected][0])

        playhead = (seconds_in * hzr) * width
        pygame.draw.rect(display, RED, (playhead, 100, 1, 200))

        # Display seconds footer
        display.blit(onesurf, (1*hzr*width, D_HEIGHT-50))
        display.blit(twosurf, (2*hzr*width, D_HEIGHT-50))
        display.blit(threesurf, (3*hzr*width, D_HEIGHT-50))

        # Display waveform
        for i, all_ in enumerate(alls):
            height = (all_/32767)*D_HEIGHT
            height /= 7
            pygame.draw.rect(display, WHITE, (
                i*width, baseline-height/2, 1, height))

        pygame.display.update()


if __name__ == '__main__':
    main()
