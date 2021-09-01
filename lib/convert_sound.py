from acb import ACBFile
import subprocess
import os
from tempfile import mkstemp

HCA_DEC = os.path.join(os.path.dirname(__file__), "hca.exe")

def hca_to_wav(src: str, dst: str, del_src: bool = True):
    ret = subprocess.call([HCA_DEC, src, "-o", dst])
    if ret == 0 and del_src:
        os.unlink(src)
    return ret

def sound_to_wav(src_folder: str, cue_name, dst_fp: str, hca_keys = None):
    # 1. set acb and awbfile
    acb_file = ""
    awb_file = ""
    for f in os.listdir(src_folder):
        if f.endswith(".acb"):
            acb_file = os.path.join(src_folder, f)
        elif f.endswith(".awb"):
            awb_file = os.path.join(src_folder, f)
    
    if not acb_file and awb_file:
        return 1

    with ACBFile(acb_file, extern_awb=awb_file, hca_keys=hca_keys) as acb:
        track = (track for track in acb.track_list.tracks if track.name == cue_name).__next__()
        f, fp = mkstemp()

        with open(fp, "wb") as out_file:
            out_file.write(acb.get_track_data(track))
        
        os.close(f)
        hca_to_wav(fp, dst_fp, True)
