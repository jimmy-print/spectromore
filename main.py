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

audiofilename = 'untitleda.wav'
with open(audiofilename, 'rb') as f:
    raw_data = f.read()
    hexadecimal_string_data = [hex(n)[2:].zfill(2) for n in raw_data]

with wave.open(audiofilename, 'rb') as wavefile:
    samples_per_second = wavefile.getparams().framerate

print()
print(f'Loading file: {audiofilename}')
print(f'Sample rate: {samples_per_second} hz')
print()

seconds_to_load = 1
samples_to_load = samples_per_second * seconds_to_load
d = hexadecimal_string_data[80:80 + samples_to_load * 2]
# mul. by 2 because 16 bit signed int means 2 bytes compose each sample.

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
    px_width_per_sample = D_WIDTH / samples_to_load
    baseline = D_HEIGHT/8

    index = 0
    index_change = 0
    px_width_per_sample_change = 0

    pygame.font.init()
    font = pygame.font.SysFont('Consolas', 15)

    onesurf = font.render('1', False, WHITE)
    twosurf = font.render('2', False, WHITE)
    threesurf = font.render('3', False, WHITE)

    def get_freqs_and_amplitudes(hzrrange0, hzrrange1):
        firstsplice = alls[int(samples_per_second * hzrrange0):int(samples_per_second * hzrrange1)]

        X = np.fft.fft(firstsplice)
        sample_amt = len(X)
        n = np.arange(sample_amt)
        T = sample_amt/samples_per_second
        freq = n/T
        freqq = np.delete(freq, 0)

        XX = np.delete(X, 0)
        XXX = np.abs(XX)

        XXXX = np.array_split(XXX, 2)[0]
        freqqq = np.array_split(freqq, 2)[0]

        return freqqq, XXXX

    starting_time = 0.01
    hzrrange0 = starting_time
    fft_interval_s = 0.01

    freq_n = len(get_freqs_and_amplitudes(hzrrange0, hzrrange0+fft_interval_s)[0])
    amplitude_n = len(get_freqs_and_amplitudes(hzrrange0, hzrrange0+fft_interval_s)[1])

    ALL_freqs = []
    ALL_amps = []

    maxs = []

    start_time = time.time()
    for nth_fft_interval in range(int((seconds_to_load - hzrrange0) / fft_interval_s)):
        freqs, amplitudes = get_freqs_and_amplitudes(hzrrange0, hzrrange0+fft_interval_s)
        maxs.append(max(amplitudes))
        try:
            assert freq_n == len(freqs)
            assert amplitude_n == len(amplitudes)
        except AssertionError:
            # insert a 0 value at the highest frequency.
            print(f'Adding new amplitude data at {nth_fft_interval * fft_interval_s} seconds')

            diff = freq_n - len(freqs)
            for i in range(abs(freq_n - len(freqs))):
                if diff < 0:
                    freqs = np.delete(freqs, -1)
                    amplitudes = np.delete(amplitudes, -1)
                elif diff > 0:
                    freqs = np.append(freqs, freqs[-1])
                    amplitudes  = np.append(amplitudes, [[0]])
            assert freq_n == len(freqs)
            assert amplitude_n == len(amplitudes)

        # At this point, the freqs is guaranteed to be the same length as the first one.
        # In other words, they are all the same size.

        ALL_freqs.append(freqs)
        ALL_amps.append(amplitudes)

        hzrrange0 += fft_interval_s

    Freqss = np.vstack(ALL_freqs)
    Amplitudess = np.vstack(ALL_amps)

    end_time = time.time()
    print(f'FFT time: {end_time - start_time} seconds')



    # generate spectrogram pixelarray
    top_vertical_margin = 200
    bottom_vertical_margin = 50

    sptg_height = D_HEIGHT - top_vertical_margin
    each_freq_band_height_px = sptg_height / freq_n
    each_time_band_width_px = fft_interval_s * samples_per_second * px_width_per_sample
    sptg_width = starting_time * samples_per_second * px_width_per_sample + each_time_band_width_px * len(Freqss)

    surf = pygame.Surface((sptg_width, sptg_height))
    print(f'pixelarray width: {surf.get_width()}, height: {surf.get_height()}')
    
    def generate_pixelarray(surf):
        pixels = pygame.PixelArray(surf)

        for ith_fft_interval, (freqs, amplitudes) in enumerate(zip(Freqss, Amplitudess)):
            for jth_freq_band, amplitude in enumerate(amplitudes):
                ratio = amplitude / max(maxs)
                hsv = colorsys.hsv_to_rgb(ratio, 0.9, 0.6*ratio+0.3)
                color = hsv[0] * 255, hsv[1] * 255, hsv[2] * 255
                
                x = (starting_time + (ith_fft_interval * fft_interval_s)) * samples_per_second * px_width_per_sample
                y = (jth_freq_band * each_freq_band_height_px)
                x_width = fft_interval_s * samples_per_second * px_width_per_sample
                y_height = each_freq_band_height_px

                for _ in range(int(x_width)):
                    for __ in range(int(y_height)):
                        pixels[int(x+_), int(y+__)] = color
        del pixels
        surf = pygame.transform.flip(surf, 0, 1)
    generate_pixelarray(surf)

    pygame.mixer.init()
    pygame.mixer.music.load(audiofilename)
    playing = False

    seconds_in = 0
    clock = pygame.time.Clock()
    frames = 0

    selected = 0
    selected_d = 0
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
                    px_width_per_sample_change = 0.001
                    px_width_per_sample += px_width_per_sample_change

                    each_time_band_width_px = fft_interval_s * samples_per_second * px_width_per_sample
                    sptg_width = starting_time * samples_per_second * px_width_per_sample + each_time_band_width_px * len(Freqss)
                    surf = pygame.Surface((sptg_width, sptg_height))
                    generate_pixelarray(surf)
                if event.key == pygame.K_DOWN:
                    px_width_per_sample_change = -0.001
                    px_width_per_sample += px_width_per_sample_change

                    each_time_band_width_px = fft_interval_s * samples_per_second * px_width_per_sample
                    sptg_width = starting_time * samples_per_second * px_width_per_sample + each_time_band_width_px * len(Freqss)
                    surf = pygame.Surface((sptg_width, sptg_height))
                    generate_pixelarray(surf)

                if event.key == pygame.K_SPACE:
                    playing = not playing
                    if playing:
                        pygame.mixer.music.play()
                        seconds_in = 0
                    else:
                        pygame.mixer.music.stop()

                if event.key == pygame.K_RIGHT:
                    selected_d = 1
                if event.key == pygame.K_LEFT:
                    selected_ = -1

            if event.type == pygame.KEYUP:
                index_change = 0
                px_width_per_sample_change = 0
                selected_d = 0

        selected += selected_d
        clock.tick()
        frames += 1
        fps = clock.get_fps()

        if playing:
            seconds_in += (1 / fps)

        index += index_change

        # Display spectrogram
        display.blit(surf, (0, D_HEIGHT - sptg_height - bottom_vertical_margin))

        # Draw selector
        pygame.draw.rect(display, WHITE, ((starting_time + fft_interval_s*selected) * px_width_per_sample * samples_per_second,
                                          750 + 10,
                                          fft_interval_s * px_width_per_sample * samples_per_second,
                                          200))

        playhead = (seconds_in * samples_per_second) * px_width_per_sample
        pygame.draw.rect(display, RED, (playhead, 100, 1, 200))

        # Display seconds footer
        display.blit(onesurf, (1 * samples_per_second * px_width_per_sample, D_HEIGHT-50))
        display.blit(twosurf, (2 * samples_per_second * px_width_per_sample, D_HEIGHT-50))
        display.blit(threesurf, (3 * samples_per_second * px_width_per_sample, D_HEIGHT-50))

        # Display waveform
        for i, all_ in enumerate(alls):
            height = (all_/32767)*D_HEIGHT
            height /= 7
            pygame.draw.rect(display, WHITE, (
                i*px_width_per_sample, baseline-height/2, 1, height))

        pygame.display.flip()


if __name__ == '__main__':
    main()
