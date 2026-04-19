## Spectromore
A spectrogram written in python with pygame and numpy

Next steps
- Live reading, playing, and generation of spectrogram
- Ability to take loaded section, edit out harmonics and replay it / save it.
  - This would require a more detailed spectrogram, also with color.
  - which in turn requires a more thorough understanding of fourier transform.

- Right now, I am not deciding the frequency bins at all.

- Use pixelarray to calculate the pixels of the spectrogram, then blit at once instead of using pygame.draw.rect in a for loop.

"Software live vocoder with monitoring

Spectrogram

For my voice: Ability to take out my own harmonics and pitch correction"
Use spectrogram to get MIDI notes from recording of piano!

![alt text](https://raw.githubusercontent.com/jimmy-print/spectromore/refs/heads/main/demo%20with%20sine%20and%20saw%20waves.png)
