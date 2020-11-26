import re
import os
import pandas as pd
import tensorflow.compat.v1 as tf

class GlobalConditioning():
#"""global conditioning class"""
  def __init__(self,csv=None,tags=None,song_bin=None,max_length=None):

    assert (tags is None) or (csv is not None ) ,'if tags is used, csv must be required'
    assert (csv is not None) or (song_bin is not None), '1 args required at reast'

    if csv is not None:
      self._df ,self._tag_lens ,self._id_dic = _get_df(csv,tags)

    self._song_bin = song_bin
    self._max_length = max_length

  def performance_to_ids(self,performance):
    ids = []
    ###tags
    if self._df is not None:
      if (performance.filename in self._df.index):
        filename = performance.filename
      else:
        tf.logging.warn("filename not in tags csv file use other")
        filename = "others"
      ids += list(self._df.loc[os.path.basename(filename)])
    #song_length
    if self._song_bin is not None:
      bin = int(floor((performance.end_time + 1 )/ self._max_length))
      assert bin < 32, 'song length is ronger than max_length!'
      ids.append(bin)

    return ids

  def get_ids(self,dic):
    #in :{tag:elem}
    #out:[id,id,id...]
    assert len(dic) == len(self._id_dic),'{} tag used but {} tag in'.format(len(self._id_dic),len(dic))
    for key in dic:
      assert key in self._id_dic, "given tag {} isn't in csv GlobalConditioning".format(key)
    ids = []
    for key in dic:
      ids.append(self._id_dic[key][dic[key]])
    return ids


  def tag_size(self):
    return len(self._tag_lens)

  def tag_lens(self):
    return self._tag_lens

  def _get_df(csv,tags):
    df = pd.DataFrame()
    for root , _ , files in os.walk(csv):
        for file in files:
            if not re.fullmatch(r'.*csv',file):
                continue
            df_tmp = pd.read_csv(os.path.join(root,file),encoding="shift-jis")
            df = pd.concat([df,df_tmp])

    df = df.set_index('file name')
    df.loc["others"] = None
    if tags is None:
        tags = df.columns
    else:
        #reform csv
        for tag in tags:
            assert tag in df.columns, "{} isnt in header !".format(tag)
        df = df[tags]

    #replace tag element to id
    tag_lens = []
    id_dic = {} #{tag:{elem:index}}
    for tag in tags:
        tag_lens.append(len(df[tag].unique()))
        id_dic[tag] = {}
        for index , elm in enumerate(df[tag].unique()):
            df = df.replace({tag: {elm:str(index)}})
            id_dic[tag][elm] = index
        df[tag] = df[tag].astype(int)
    return df,tag_lens,id_dic