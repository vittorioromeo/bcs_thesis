import time
import sys
import numpy
import math
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

dynamic_noip_50k = [3340, 3194, 3291] # mean = 3275
dynamic_noip_100k = [7293, 7627, 7314] # mean = 7411 
dynamic_noip_200k = [19034, 18952, 19704] # mean = 19230

fixed_noip_50k = [2789, 2904, 3097] # mean = 2930
fixed_noip_100k = [5961, 6830, 6962] # mean = 6584
fixed_noip_200k = [15741, 17585, 17575] # mean = 16967

dynamic_ip_50k = [2930, 3027, 3000] # mean = 2985
dynamic_ip_100k = [6241, 6295, 6176] # mean = 6237
dynamic_ip_200k = [16258, 17046, 16772] # mean = 16692

fixed_ip_50k = [3110, 2818, 2984] # mean = 2971
fixed_ip_100k = [5754, 5442, 6098] # mean = 5765 
fixed_ip_200k = [15202, 13737, 15734] # mean = 14891

# 50k noip mean = 3102
# 100k noip mean = 6997
# 200k noip mean = 18099

# 50k ip mean = 2978
# 100k ip mean = 6001
# 200k ip mean = 15792

def output_file(filename):
    return "add_del_outputs/" + filename

def conf_stats(arr):
    mean = numpy.mean(arr)
    stddev = numpy.std(arr)
    # conf = 0.95 * (stddev / math.sqrt(len(arr)))

    return (mean, stddev)

def make_overview_plot(filename, title, noip_arrs, ip_arrs):
    plt.title("Entity add/del - " + title)

    
    plt.ylabel('Time (ms)', fontsize=12)

    x = 0
    barwidth = 0.5
    bargroupspacing = 1.5

    for z in zip(noip_arrs, ip_arrs):
        noip,ip = z
        noip_mean,noip_conf = conf_stats(noip)
        ip_mean,ip_conf = conf_stats(ip)

        b_noip = plt.bar(x, noip_mean, barwidth, color='r', yerr=noip_conf, ecolor='black', alpha=0.7)
        x += barwidth

        b_ip = plt.bar(x, ip_mean, barwidth, color='b', yerr=ip_conf, ecolor='black', alpha=0.7)
        x += bargroupspacing

    plt.xticks([0.5, 2.5, 4.5], ['50k', '100k', '200k'], rotation='horizontal')

    fontP = FontProperties()
    fontP.set_size('small')

    plt.legend([b_noip, b_ip], \
        ('no inner parallelism', 'inner parallelism'), \
        prop=fontP, loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=2)
   
    plt.ylim([0,25000])
    plt.savefig(output_file(filename))
    plt.clf()

def make_entity_plot(filename, title, fixed_noip, fixed_ip, dynamic_noip, dynamic_ip):
    plt.figure(figsize=(12,5))

    plt.title("Settings comparison - " + title)
    
    plt.xlabel('Time (ms)', fontsize=12)
    plt.xlim([0,25000])

    x = 0
    barwidth = 0.5
    bargroupspacing = 1.5

    fixed_noip_mean,fixed_noip_conf = conf_stats(fixed_noip)
    fixed_ip_mean,fixed_ip_conf = conf_stats(fixed_ip)
    dynamic_noip_mean,dynamic_noip_conf = conf_stats(dynamic_noip)
    dynamic_ip_mean,dynamic_ip_conf = conf_stats(dynamic_ip)

    values = [fixed_noip_mean,fixed_ip_mean,dynamic_noip_mean, dynamic_ip_mean]
    errs = [fixed_noip_conf,fixed_ip_conf,dynamic_noip_conf, dynamic_ip_conf]

    y_pos = numpy.arange(len(values))
    plt.barh(y_pos, values, xerr=errs, align='center', color=['r', 'b', 'r', 'b'],  ecolor='black', alpha=0.7)
    plt.yticks(y_pos, ["Fixed | no I.P.", "Fixed | I.P.", "Dynamic | no I.P.", "Dynamic | I.P."])
    plt.savefig(output_file(filename))
    plt.clf()


if __name__ == "__main__":
    make_overview_plot("ipcomp_dynamic.png", "dynamic entity storage", \
        [dynamic_noip_50k, dynamic_noip_100k, dynamic_noip_200k], \
        [dynamic_ip_50k, dynamic_ip_100k, dynamic_ip_200k])

    make_overview_plot("ipcomp_fixed.png", "fixed entity storage", \
        [fixed_noip_50k, fixed_noip_100k, fixed_noip_200k], \
        [fixed_ip_50k, fixed_ip_100k, fixed_ip_200k])

    make_entity_plot("entity_50k.png", "50000 entities", \
        fixed_noip_50k, fixed_ip_50k, \
        dynamic_noip_50k, dynamic_ip_50k)

    make_entity_plot("entity_100k.png", "100000 entities", \
        fixed_noip_100k, fixed_ip_100k, \
        dynamic_noip_100k, dynamic_ip_100k)

    make_entity_plot("entity_200k.png", "200000 entities", \
        fixed_noip_200k, fixed_ip_200k, \
        dynamic_noip_200k, dynamic_ip_200k)