import os
import time
import pandas as pd
import numpy as np
import ovito
from ovito.modifiers import CalculateDisplacementsModifier, ExpressionSelectionModifier
print("Hello, this is OVITO %i.%i.%i" % ovito.version)


def sum_modify(frame, data):
    #自定义OVITO处理函数，目前已弃用
    Shear_datas = data.particles['Structure Type']
    Total_Shear = np.sum(Shear_datas)/len(Shear_datas)
    data.attributes['Total_Shear'] = Total_Shear

def find_center(frame, data):
    #寻找dump文件中的形状中心
    Coord = data.particles.positions#返回一个[原子数，[x,y,z]]的矩阵
    nX = np.sum(Coord[:,0])/len(Coord)
    nY = np.sum(Coord[:,1])/len(Coord)
    nZ = np.sum(Coord[:,2])/len(Coord)
    #该计算方法完成后，不能直接return值，而是将其传递给全局变量data.attributes中保存
    data.attributes['nX'] = nX
    data.attributes['nY'] = nY
    data.attributes['nZ'] = nZ



def calculate_strain(filepath,outpath,i):#函数名字并不重要
    #这里的函数是为了计算dump文件中的晶体结构的原子数量
    #文件序列
    filestream = filepath + '/' + 'degree.'+ str(i) +'.*.atom'
    #打印当前的文件序列
    print(filestream)
    # 将文件使用ovito.io.import的方式导入到ovito中
    pipeline = ovito.io.import_file(filestream)
    # 打印该序列中文件的总数
    print("total_frames : %d" % pipeline.source.num_frames)
    #将我们先前自定义的方法添加到modifier中
    pipeline.modifiers.append(find_center) 
    #设定参考帧
    #每次需要选择特定的帧进行计算时，需要使用pipeline.compute（）函数以完成modifier的应用
    refer_data = pipeline.compute(frame = pipeline.source.num_frames)
    ##使用CNA进行modify的操作
    # pipeline.modifiers.append(ovito.modifiers.CommonNeighborAnalysisModifier(
    #     mode = ovito.modifiers.CommonNeighborAnalysisModifier.Mode.AdaptiveCutoff
    # ))
    ##使用PTM进行modify的操作
    pipeline.modifiers.append(ovito.modifiers.PolyhedralTemplateMatchingModifier(
        rmsd_cutoff =  2
    ))
    ##使用Atomic Strain进行modify的操作
    # pipeline.modifiers.append(ovito.modifiers.AtomicStrainModifier(
    #     cutoff = 4.32,
    #     use_frame_offset = False,
    #     reference_frame = 5
    # ))
    #使用Coordination analysis进行modify操作
    pipeline.modifiers.append(ovito.modifiers.CoordinationAnalysisModifier(
        cutoff = 12,
        number_of_bins = 200
    ))
    #使用Expression Selection进行modify操作
    pipeline.modifiers.append(ovito.modifiers.ExpressionSelectionModifier(
        expression = 'Coordination <= 400'
    ))
    #使用DeleteSelected进行modify操作
    pipeline.modifiers.append(ovito.modifiers.DeleteSelectedModifier(

    ))
    ##使用反选操作
    # pipeline.modifiers.append(ovito.modifiers.ExpressionSelectionModifier(
    #     expression = '(Position.Z^2+Position.Y^2)<=100'
    # ))
    #同上EXpression Selection
    pipeline.modifiers.append(ovito.modifiers.ExpressionSelectionModifier(
        expression = 'Position.X<={} || Position.X >={}'.format(refer_data.attributes['nX']-5, refer_data.attributes['nX']+5)
    ))
    ##同上反选操作
    # pipeline.modifiers.append(ovito.modifiers.InvertSelectionModifier(
    #     operate_on = 'particles'
    # ))
    #同上删除操作
    pipeline.modifiers.append(ovito.modifiers.DeleteSelectedModifier(

    ))
    # 对文件序列中的 某 帧之后的数据进行计算
    ## 使用pipeline.source.num_frames 访问总帧数，返回int
    for j in range(pipeline.source.num_frames-1,pipeline.source.num_frames):
        if j % 100 == 0:
            print("Running...",end = '\r')
        #每次循环对当前帧数应用前述所有modifier
        data = pipeline.compute(frame = j) 
        #计算晶体原子数量所占百分比
        num = np.count_nonzero(data.particles['Structure Type'])/len(data.particles['Structure Type'])
    #输出，并return
    Out_put_data = num
    # 返回计算完成的结果
    return Out_put_data
## 现在需要依次读取每个文件夹中的文件，进行计算后输出到一个csv文件中，进行数据处理，不同温度节点下的数据    
## 以下与各自的文件结构有关，不做注释。
path = r'/Volumes/xxxxxxxxxx/data/'
os.chdir(path)
folders = os.listdir(path)
result_lie = pd.DataFrame()
lie_initiate = 0 
for folder in folders:
    print("Now at the Temperautre of {}.".format(str(folder)))
    #储存对应温度下的应变数据
    result_df = []
    folderpath = path + '/' + folder
    result_folder = folderpath + '/result/'
    os.chdir(result_folder)
    for i in range(1,11,1):
        dump_dir = result_folder + '/' + str(i) + '/'
        #调用前面的ovito操作函数
        Out_put_data = calculate_strain(dump_dir, path, i)
        result_df.append(Out_put_data)
    result_pd = pd.DataFrame({'{}'.format(folder): result_df}  )
    print(result_df)
    os.chdir(path)
    result_lie = pd.concat([result_lie,result_pd], axis = 1)
os.chdir(path)
result_lie.to_csv("列数据.csv")
