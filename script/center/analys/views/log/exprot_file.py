# -*- coding: utf-8 -*-

import os, shutil, json
from django.http import HttpResponse
import sys
import codecs
 
import datetime
from settings import STATIC_ROOT,STATIC_URL
import codecs
import shutil
import re

class ExportPath:
    
    @classmethod
    def mkdir(self,path):
        if not os.path.exists(path):
            os.makedirs(path, 0755)
            
    @classmethod
    def get_export_root_dir(cls):
        the_dir = os.path.join(STATIC_ROOT,'export')
        cls.mkdir(the_dir)
        return the_dir
    
    @classmethod
    def make_export_dir(cls,path):
        the_dir = os.path.join(cls.get_export_root_dir(),path)
        cls.mkdir(the_dir)
        return the_dir
    
    @classmethod
    def get_url(cls,key_name):
        return '%sexport/%s' % (STATIC_URL,key_name)
    
    @classmethod
    def get_dir(cls,key_name):
        return cls.make_export_dir(key_name)
    
    @classmethod
    def get_export_query_dir(cls):
        return cls.get_dir('query')

    @classmethod
    def get_export_card_dir(cls):
        return cls.get_dir('card')
    
    @classmethod
    def get_export_query_url(cls):
        return cls.get_url('query')
        
    @classmethod
    def get_export_card_url(cls):
        return cls.get_url('card')
    

            
    
class ExportFile(object):
    '''文件导出
    '''
    ROOT_DIR = ExportPath.get_export_root_dir()
    TYPE_MAP = {1:{"suffix":".xls"},
                2:{"suffix":".csv"},
                3:{"suffix":".txt"},
                }
    
    def __init__(self,export_key,export_type=1):
        self.export_key = export_key.strip()
        self.export_type = int(export_type)
        self.save_dir = os.path.join(self.ROOT_DIR,export_key)
        self.merge_file_name = self.export_key + self.TYPE_MAP[self.export_type]['suffix']
        self.merge_file_path = os.path.join(self.ROOT_DIR,self.merge_file_name)
        self.create_save_dir()
            
    def create_save_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, 0766)
    def get_files(self):
        for file_name in os.listdir(self.save_dir):
            file_path = os.path.join(self.save_dir,file_name)
            yield file_path
            
    def clear_files(self):
        for file_path in self.get_files():
            if os.path.isfile(file_path):
                #print 'delete %s' % file_path
                os.remove(file_path)
        os.rmdir(self.save_dir)
        
    def merge_files(self,fields):
        '''合并文件
        @param merge_file_name:合并的文件名
        '''
        fp = codecs.open(self.merge_file_path, 'wb','utf-8')
        fp.write(codecs.BOM_UTF8)
        
        if self.export_type == 1:
            head_str = self.excel_convert(True, [], fields, False) 
        if self.export_type == 2:
            head_str = self.csv_convert(True, [], fields, False)
        elif self.export_type == 3:
            head_str = self.txt_convert(True, [], fields, False) 
            
        fp.write(head_str)
        for file_path in self.get_files():
            rfp = open(file_path,'rb')
            for line in rfp:
                fp.write(line)
            rfp.close()
            fp.flush()
            
        if self.export_type == 1:
            fp.write('</table>')
        fp.close()
        self.clear_files()
        
    def csv_convert(self, is_create, list_data, fields, is_finish=False):
        file_str = '%s%s'
        head_str = ''
        the_item_handler = lambda x :  '"%s\t"' % str(x).replace('"','""')  if str(x).isdigit() and len(str(x))>=15 else '"%s"' % str(x).replace('"','""')
        if is_create : 
            head_str = ','.join([ the_item_handler(x).replace('\n','') for x  in  fields])
            head_str = '%s\n' % head_str
         
        row_str = ''
        for items in list_data:
            item_str = ''
            if items:
                item_str = ','.join([   the_item_handler(x).replace('\n','') for x  in  items])
                row_str += '%s\n' % item_str
        
        file_str = file_str % (head_str, row_str)
        
        return file_str
    
    def excel_convert(self, is_create, list_data, fields, is_finish=False):
        file_str = '%s%s'
        
        head_str = ''
        if is_create : 
            for field in fields: 
                head_str += '<td>%s</td>'%field
            head_str = '<table><tr>%s</tr>\n'%head_str
         
        row_str = ''

        for items in list_data:
            item_str = ''
            for item in items or []:
                item_str += '<td>%s</td>'%item
        
            row_str += '<tr>%s</tr>\n'%item_str
        
        file_str = file_str % (head_str, row_str)
     
        if is_finish:
            file_str += u'</table>' 
        
        return file_str
    
    def txt_convert(self, is_create, list_data, fields, is_finish=False):  
        head_str = ''
        row_str = ''
        if fields != '' and is_create and str(fields).find('feiyin') != 0 :
            head_str = '\t'.join([ str(x).replace('\n','') for x  in  fields])
            head_str = '%s\n' % head_str 
                       
        for items in list_data:
            item_str = ''
            if items:
                item_str = '\t'.join([ str(x).replace('\n','') for x  in  items])
                row_str += '%s\n'%item_str
        
        file_str = '%s%s' % (head_str, row_str)

        return file_str 
    
    
#汇总生成的文件的方法    
    def summary_file(self,merges=[],keyfunc=lambda x:x[0]):
        '''
        @param merges: 需要合并的列索引
        '''
        self.summary_file_name = self.merge_file_name
        self.summary_file_path = os.path.join(self.ROOT_DIR,self.merge_file_name)
        self.suffix = os.path.splitext(self.summary_file_name)[1]
        handlers = {'.txt':[lambda x :x.split('\t'),self.txt_convert],
                    '.csv':[lambda x :x.strip('"').split('","'),self.csv_convert],
                    '.xls':[lambda x :x.replace('<table>','').replace('</table>','').replace('<tr>','').replace('</tr>','').replace('</td>','').replace('<td>',' ').split(),self.excel_convert],

        
        }
        self.head_strs = []
        self.handler = handlers[self.suffix]
        self._d = {}
        self._merges = merges
        self.keyfunc = keyfunc
        return self.get_summary_file_name()

        
    def get_summary_file_name(self):
        done_summary_file_name = 'summary_%s' % self.merge_file_name
        done_summary_file_path = os.path.join(self.ROOT_DIR,done_summary_file_name)
        _str = self.get_result()
        fp = codecs.open(done_summary_file_path, 'wb','utf-8')
        fp.write(codecs.BOM_UTF8)
        fp.write(_str)
        fp.close()
        self.clear_files()
        return done_summary_file_name

    def get_result(self):
        self._make_result()
        return self.handler[1](is_create=True, list_data=self._d.values(), fields=self.head_strs)
        
    def _merge_items(self,sl,tl):
        sl_len = len(sl)
        tl_len = len(tl)
        for i in self._merges:
            try:
                if sl_len >= i and  tl_len >= i and tl[i].isdigit():
                    sl[i] = int(sl[i]) + int(tl[i])
            except:
                pass
    def _summary_line(self,line):
            items = self.handler[0](line)
            if items:
                if not self._merges:
                    self._merges = range(1,len(items))
                k = self.keyfunc(items)
                if self._d.has_key(k):
                    self._merge_items(self._d[k],items)
                else:
                    self._d[k] = items

    def _make_result(self):
        f = open(self.summary_file_path,'rb')
        self.head_strs =  self.handler[0](f.readline().strip(codecs.BOM_UTF8).strip())#第一行为标题
        for line in  f:
            if line:
                self._summary_line(line.strip())
        f.close()
        return self._d     
         
    def gene_file(self,file_name,list_data, fields, page_num, page_size, total_record):
        has_next = True
        de = total_record / page_size
        
        if total_record % page_size >= 1:
            total_page =  de + 1 
        else:
            total_page =  de
        if page_num + 1 > total_page:
            has_next = False
        
        self.file_path = os.path.join(self.save_dir, file_name)
        self.write_file( self.file_path,list_data,page_num)
        
        page_num += 1
        is_finish = not has_next
        result = {"page_num":page_num, "has_next": has_next, "total_page": total_page, "export_key":self.export_key,"is_finish":is_finish}
        
        return result
    
    def write_file(self, file_path, list_data, page_num):
        if page_num <= 1 :
            if os.path.exists(file_path):
                os.remove(file_path)
            fp = codecs.open(file_path, 'wb','utf-8')
        else:
            fp = codecs.open(file_path, 'ab','utf-8')
            
        if self.export_type == 1:
            file_str = self.excel_convert(False, list_data, fields=[], is_finish=False)    
        elif self.export_type == 2:
            file_str = self.csv_convert(False, list_data, fields=[], is_finish=False)
        elif self.export_type == 3:
            file_str = self.txt_convert(False, list_data, fields=[], is_finish=False)    

        fp.write(file_str)
        fp.flush()
        fp.close()
         
            
class QueryExprot(ExportFile):
    '''查询导出
    '''
    def __init__(self,export_key,export_type):
        self.ROOT_DIR =  ExportPath.get_export_query_dir()
        super(QueryExprot,self).__init__(export_key,export_type)
        
    def merge_files(self,fields):
        super(QueryExprot,self).merge_files(fields)
        return self.merge_file_name
    

class CardExport(ExportFile):
    '''礼包卡导出
    '''
    def __init__(self,export_key,export_type):
        self.ROOT_DIR =  ExportPath.get_export_card_dir()
        super(CardExport,self).__init__(export_key,export_type)
    
    
    def gene_file(self,*args,**kwargs):
        _r = super(CardExport,self).gene_file(*args,**kwargs)
        if _r['is_finish']:
            fields = kwargs.get('fields',[])
            print fields
            self.merge_files(fields)
            _r['url'] = '%s/%s' % (ExportPath.get_export_card_url(),self.merge_file_name)
        return _r
        
        