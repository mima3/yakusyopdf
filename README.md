# �ړI
�����J���Ȃ����J���Ă���[�V�^�R���i�E�C���X�����ǂ̊����g��𓥂܂����I�����C���f�Âɂ���](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/rinsyo/index_00014.html)��PDF����CSV��JSON�ɕϊ����āA�R���s���[�^�ŏ��������₷���悤�ɂ��܂��B

�����ɂ��Ă͉��L���Q�Ƃ��Ă��������B
https://needtec.sakura.ne.jp/wod07672/2020/04/29/%e5%8e%9a%e7%94%9f%e5%8a%b4%e5%83%8d%e6%89%80%e3%81%aepdf%e3%82%92csv%e3%82%84json%e3%81%ab%e5%a4%89%e6%8f%9b%e3%81%99%e3%82%8b/


## �ˑ����郉�C�u����
 - |beautifulsoup4
 - opencv-python
 - camelot-py
 - mojimoji
 - requests
 - tqdm

## �g�p���@

```
# �V�^�R���i�E�C���X�����ǂ̊����g��𓥂܂����I�����C���f�Âɂ��Ẵy�[�W����PDF���_�E�����[�h���ăt�H���_�ɕۑ�����
python download_pdf.py

# �쐬�����t�H���_���w�肵�āAPDF�̓��e����JSON��CSV���쐬����
python analyze_pdf.py 20200428

# �e�s���{�����Ƃ�JSON�t�@�C����1�̃t�@�C���ɓZ�߂܂��B�܂��A���̍ہA�L�[���Z�����ɂ��܂��B
python merge_json 20200428

# Yahoo�̃W�I�R�[�_API��p���ďZ������o�x�E�ܓx�����߂čX�V���܂��B
python create_geo.py 20200428 Yahoo��APPID

# �W�I�R�[�_API�̎g�p�ʂ����炷���߁A�ȑO�쐬�����o�x�ܓx�����C���|�[�g���邱�Ƃ��\�ł�
python create_geo_by_json.py �Â�all_data.json �V����all_data.json

# �f�[�^�x�[�X�ɕۑ����܂�
python create_hospital_db.py 20200428\all_data.json 20200428\hospital.sqlite
```

## ���C�Z���X
MIT
