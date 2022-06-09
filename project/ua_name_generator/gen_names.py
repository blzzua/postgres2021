import random
from numpy.random import choice

with open('checked/SURNAMES.count', 'r') as f:
    FM_count = [ (int(cnt), mname, int(mcnt), (fname), fcnt) for  cnt, mname, mcnt, fname, fcnt in map(str.split, f.readlines()) ]

global_surnames_list = [mname for cnt, mname, mcnt, fname, fcnt in FM_count]
global_surnames_dict_list = [ { 'cnt':cnt, 'mname':mname, 'mcnt':mcnt, 'fname':fname, 'fcnt':fcnt}  for  cnt, mname, mcnt, fname, fcnt in FM_count ]
global_surnames_freq = [cnt  for cnt, mname, mcnt, fname, fcnt in FM_count ]
global_surnames_sum = sum(global_surnames_freq)
global_surnames_probab = [ i/global_surnames_sum for i in global_surnames_freq ]

with open('checked/FEMALE_I.count') as f:
     name_count_f = [ ('F', int(cnt),name.strip()) for cnt,name in map(str.split, f.readlines()) ]
with open('checked/MALE_I.count') as f:
     name_count_m = [ ('M',int(cnt),name.strip()) for cnt,name in map(str.split, f.readlines()) ]
name_count_list = name_count_f + name_count_m

global_name_list = [name for gender, cnt, name in name_count_list ]
global_names_freq = [cnt for gender, cnt, name in name_count_list ]
global_names_sum = sum(global_names_freq)
global_names_sum_probab = [ i/global_names_sum for i in global_names_freq ]

global_fname_list = [name for gender, cnt, name in name_count_f ]
global_fnames_freq = [cnt for gender, cnt, name in name_count_f ]
global_fnames_sum = sum(global_fnames_freq)
global_fnames_sum_probab = [ i/global_fnames_sum for i in global_fnames_freq ]

global_mname_list = [name for gender, cnt, name in name_count_m ]
global_mnames_freq = [cnt for gender, cnt, name in name_count_m ]
global_mnames_sum = sum(global_mnames_freq)
global_mnames_sum_probab = [ i/global_mnames_sum for i in global_mnames_freq ]

with open('checked/PATRONIC.count') as f:
     patronic_count = [ (gender, int(cnt), oname.strip(), pname.strip()) for gender, cnt, oname, pname in map(str.split, f.readlines()) ]
global_fpatronics_list = [pname for gender, cnt, oname, pname  in filter(lambda o: o[0] == 'F', patronic_count) ]
global_fpatronics_freq = [cnt for  gender, cnt, oname, pname in filter(lambda o: o[0] == 'F', patronic_count) ]
global_fpatronics_sum = sum(global_fpatronics_freq)
global_fpatronics_sum_probab = [ i/global_fpatronics_sum for i in global_fpatronics_freq ]

global_mpatronics_list = [pname for gender, cnt, oname, pname  in filter(lambda o: o[0] == 'M', patronic_count) ]
global_mpatronics_freq = [cnt for  gender, cnt, oname, pname in filter(lambda o: o[0] == 'M', patronic_count) ]
global_mpatronics_sum = sum(global_mpatronics_freq)
global_mpatronics_sum_probab = [ i/global_mpatronics_sum for i in global_mpatronics_freq ]

def gen_fio(format_= 'dict', gender = 'U'):
    """
    generate fio
    TODO formats support:
    format_ output format 'fio' | 'iof' | 'fi' | 'dict'
    'fio' 'ШЕВЧЕНКО ОЛЕКСАНДР МИКОЛАЙОВИЧ' 
    'iof' 'ОЛЕКСАНДР МИКОЛАЙОВИЧ ШЕВЧЕНКО' 
    'fi' 'ШЕВЧЕНКО ОЛЕКСАНДР' 
    'dict' {'f': 'ШЕВЧЕНКО', 'i': 'ОЛЕКСАНДР', 'o': 'МИКОЛАЙОВИЧ', 'gender': 'M' }
    """
    if gender not in ('F','M'):
        gender = choice(('F','M'))
    d = choice(global_surnames_dict_list, size=1,  replace=True, p=global_surnames_probab)[0]
    if gender == 'F':
        i = choice(global_fname_list, size=1,  replace=True, p=global_fnames_sum_probab)[0]
        f = d['fname']
        o = choice(global_fpatronics_list, size=1,  replace=True, p=global_fpatronics_sum_probab)[0]
    elif gender == 'M':
        i = choice(global_mname_list, size=1,  replace=True, p=global_mnames_sum_probab)[0]
        f = d['mname']
        o = choice(global_mpatronics_list, size=1,  replace=True, p=global_mpatronics_sum_probab)[0]
    d = {'f': f, 'i': i, 'o': o, 'gender': gender}
    return (d)

def gen_husband_fio(person):
    """generate fio husband for person. person - dict must have keys f, gender"""
    if person['gender'] == 'F':
        gender = 'M'
        d = next(filter(lambda o: o['fname'] == person['f'], global_surnames_dict_list ))
    elif person['gender'] == 'M':
        gender = 'F'
        d = next(filter(lambda o: o['mname'] == person['f'], global_surnames_dict_list ))
    else:
        # WTF
        gender = choice(('F','M'))
        d = choice(global_surnames_dict_list, size=1,  replace=True, p=global_surnames_probab)[0]
    if gender == 'F':
        i = choice(global_fname_list, size=1,  replace=True, p=global_fnames_sum_probab)[0]
        f = d['fname']
        o = choice(global_fpatronics_list, size=1,  replace=True, p=global_fpatronics_sum_probab)[0]
    elif gender == 'M':
        i = choice(global_mname_list, size=1,  replace=True, p=global_mnames_sum_probab)[0]
        f = d['mname']
        o = choice(global_mpatronics_list, size=1,  replace=True, p=global_mpatronics_sum_probab)[0]
    d = {'f': f, 'i': i, 'o': o, 'gender': gender}
    return (d)

if __name__ == '__main__':
    for i in range(1):
        pers  = gen_fio()
        print(pers,gen_husband_fio(pers))

