import re
import os
import pandas as pd
import tensorflow.compat.v1 as tf

class GlobalConditioning():
#"""global conditioning class"""
  def __init__(self,csv=None,tags=None):

    assert (tags is None) or (csv is not None ) ,'if tags is used, csv must be required'

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
    self._df = df
    self._tag_lens = tag_lens
    self._id_dic = id_dic

  def filename_to_ids(self,filename):
    if not (filename in self._df.index):
      tf.logging.warn("filename not in tags csv file use other")
      filename = "others"
    return list(self._df.loc[os.path.basename(filename)])

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