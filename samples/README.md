# Demo samples

Real HAM10000 dermoscopy images taken from the **test split** of the lesion-wise split (seed 42), so the model never saw them or any other photo of the same lesions during training or validation. The split was reproduced from the original HAM10000 metadata and checked against the counts printed by the Kaggle notebook (7,054 / 1,464 / 1,497 images).

For each class there are up to two images the model gets right with the highest confidence and one it gets wrong or is least sure about, so you can show both the strengths and the weaknesses. The last two columns were produced by the trained model in `models/best.pt`.

Images: Tschandl et al., HAM10000 (CC BY-NC 4.0), downloaded from the ISIC archive.

| File | True class | Model says | Confidence | Melanoma probability |
|---|---|---|---|---|
| akiec_1_ISIC_0032404.jpg | akiec | akiec (correct) | 100% | 0% |
| akiec_2_ISIC_0026212.jpg | akiec | akiec (correct) | 97% | 1% |
| akiec_3_ISIC_0025178.jpg | akiec | df (WRONG) | 95% | 1% |
| bcc_1_ISIC_0034155.jpg | bcc | bcc (correct) | 100% | 0% |
| bcc_2_ISIC_0033001.jpg | bcc | bcc (correct) | 100% | 0% |
| bcc_3_ISIC_0031450.jpg | bcc | bkl (WRONG) | 99% | 0% |
| bkl_1_ISIC_0031831.jpg | bkl | bkl (correct) | 100% | 0% |
| bkl_2_ISIC_0029897.jpg | bkl | bkl (correct) | 100% | 0% |
| bkl_3_ISIC_0034040.jpg | bkl | nv (WRONG) | 89% | 6% |
| df_1_ISIC_0031271.jpg | df | df (correct) | 100% | 0% |
| df_2_ISIC_0024845.jpg | df | df (correct) | 99% | 0% |
| df_3_ISIC_0033860.jpg | df | nv (WRONG) | 93% | 1% |
| mel_1_ISIC_0032940.jpg | mel | mel (correct) | 98% | 98% |
| mel_2_ISIC_0032684.jpg | mel | mel (correct) | 96% | 96% |
| mel_3_ISIC_0027797.jpg | mel | nv (WRONG) | 84% | 16% |
| nv_1_ISIC_0031072.jpg | nv | nv (correct) | 100% | 0% |
| nv_2_ISIC_0025965.jpg | nv | nv (correct) | 100% | 0% |
| nv_3_ISIC_0024975.jpg | nv | mel (WRONG) | 87% | 87% |
| vasc_1_ISIC_0031201.jpg | vasc | vasc (correct) | 100% | 0% |
| vasc_2_ISIC_0026876.jpg | vasc | vasc (correct) | 100% | 0% |
| vasc_3_ISIC_0029877.jpg | vasc | nv (WRONG) | 80% | 0% |
