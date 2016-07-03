import time
import sys
import numpy
import math
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

dynamic_noip_50k = [9499, 9180, 9383] # mean = 9354
dynamic_noip_100k = [22734, 21890, 21922] # mean = 22182 
dynamic_noip_200k = [61441, 59399, 58905] # mean = 59915

fixed_noip_50k = [9046, 9213, 9177] # mean = 9145
fixed_noip_100k = [22423, 21536, 21653] # mean = 21870
fixed_noip_200k = [59312, 56163, 58088] # mean = 57854

dynamic_ip_50k = [3176, 3218, 4039] # mean = 3477
dynamic_ip_100k = [6932, 7240, 8008] # mean = 7393
dynamic_ip_200k = [19135, 18150, 20747] # mean = 19344

fixed_ip_50k = [3683, 3700, 3098] # mean = 3493
fixed_ip_100k = [7769, 7693, 6778] # mean = 7413 
fixed_ip_200k = [20314, 19480, 18501] # mean = 19431

# 50k noip mean = 9249
# 100k noip mean = 22026
# 200k noip mean = 58884

# 50k ip mean = 3485
# 100k ip mean = 7403
# 200k ip mean = 19387

def output_file(filename):
    return "outputs/" + filename

def conf_stats(arr):
    mean = numpy.mean(arr)
    stddev = numpy.std(arr)
    # conf = 0.95 * (stddev / math.sqrt(len(arr)))

    return (mean, stddev)

def make_overview_plot(filename, title, noip_arrs, ip_arrs):
    plt.title("Inner parallelism - " + title)

    
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
   
    plt.ylim([0,62000])
    plt.savefig(output_file(filename))
    plt.clf()

def make_entity_plot(filename, title, fixed_noip, fixed_ip, dynamic_noip, dynamic_ip):
    plt.figure(figsize=(12,5))

    plt.title("Settings comparison - " + title)
    
    plt.xlabel('Time (ms)', fontsize=12)
    plt.xlim([0,62000])

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