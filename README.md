# audio-watermark-auth

Lab nay minh hoa co che xac thuc audio bang spread-spectrum self-marking watermark.
Watermark duoc nhung tren nhieu frame audio bang day gia ngau nhien tao tu key.
Khi kiem tra, chuong trinh do tuong quan giua watermark ky vong va audio dau vao
de phan loai thay doi thanh `ACCEPTABLE`, `SUSPICIOUS`, hoac `MALICIOUS`.

Tap trung cua lab:

- Nhung watermark robust vao `cover.wav`.
- Gom tat ca bien doi trong mot file `attack.py`.
- Demo 3 bien doi chinh trong huong dan: `volume`, `noise`, `crop`.
- Cac bien doi khac van co san: `lowpass`, `replace`, `reorder`.

Luong thuc hanh:

```bash
cd ~/stego
python3 ss_selfmark_embed.py cover.wav marked_ss.wav --key 12345
python3 attack.py marked_ss.wav volume.wav --type volume --factor 0.8
python3 attack.py marked_ss.wav noise.wav --type noise --snr 30
python3 attack.py marked_ss.wav cropped.wav --type crop --ratio 0.1
python3 ss_selfmark_verify.py volume.wav --key 12345
python3 ss_selfmark_verify.py noise.wav --key 12345
python3 ss_selfmark_verify.py cropped.wav --key 12345
```
