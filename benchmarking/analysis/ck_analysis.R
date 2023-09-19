library(ggplot2)
library(dplyr)
library(ggpubr)
library(rstatix)
library(plyr)

setwd("~/Work/Software/fond-compact-asp/benchmarking/analysis")
df_ck = read.csv("./ck_results.csv")
df_ckp = read.csv("./ck_result_plots.csv")

domain_levels = c( "spiky-tireworld", "miner","tireworld-truck",  "islands", "blocksworld-ipc08", "first-responders-ipc08")
domain_labels = c("Spiky-T (9)", "Miner (49)","T-Truck (74)",  "Islands (60)", "Blocksworld", "First Resp.")
df_ckp$domain = factor(df_ckp$domain, levels = domain_levels, labels=domain_labels)
df_ckp$planner = factor(df_ckp$planner, levels = c("CASP-Base", "CASP-KB"))

compare_means(time ~ planner, df_ckp, method = "wilcox.test", paired = TRUE, group.by = c("domain"))

medians = ddply(df_ckp, .(domain, planner), summarize, count = length(instance), med = round(median(time),1))

p = ggplot(df_ckp, aes(time, planner))
p = p + geom_boxplot(size=0.5, aes(color=planner), show.legend = F, linewidth=0.25) + stat_compare_means(comparisons = list(c("CASP-Base", "CASP-KB")), aes(label=..p.signif.., group=c("domain")),vjust=2,method = "wilcox.test", paired=T)
p = p + facet_wrap(~domain, ncol=3,strip.position="right", scales="free_x") + expand_limits(x = 100)
p = p + stat_summary(fun=mean, colour="darkred", geom="point", 
                     shape=18, size=2, show.legend=FALSE) + 
  geom_text(data = medians, aes(label = med, y = planner, x=med), size=3, vjust=-0.5,hjust=-0.9)
p + xlab("Time (sec)") + ylab("Compact ASP Planners")


ggsave("ck_results_reg.pdf", width=7, height=2.5, units="in", dpi=300)


domains_with_ck = c("blocksworld-ipc", "first-responders-ipc08", "islands", "miner", "spiky-tireworld", "tireworld-truck")
df_ck = subset(df_ck, domain %in% domains_with_ck)

df_ck$planner[df_ck$planner == 'asp2-reg-4h'] = "asp2"
df_ck$planner[df_ck$planner == 'asp2-reg-undo-4h'] = "asp2-u"
df_ck$planner[df_ck$planner == 'asp2-reg-kb-4h'] = "asp2-k"

group_by(df_ck, domain, planner) %>%
  summarise(
    count = n(),
    median = median(time, na.rm = TRUE),
    #IQR = IQR(time, na.rm = TRUE),
    mean = mean(time, na.rm = TRUE)
  )

## WE will use paired wilcox test
## Miner has undo and domain kb
choice = c("asp2", "asp2-k")
df_1 = subset(df_ck, domain == "miner" & planner %in% choice)
i_1 = df_1[df_1$planner == choice[1],]$instance
i_2 = df_1[df_1$planner == choice[2],]$instance
intersection = intersect(i_1, i_2)
df_1 = subset(df_1, instance %in% intersection)
df_1$planner = factor(df_1$planner, levels = choice)
wilcox.test(df_1$time ~ df_1$planner, paired=TRUE)

group_by(df_1, domain, planner) %>%
  summarise(
    count = n(),
    median = median(time, na.rm = TRUE),
    #IQR = IQR(time, na.rm = TRUE),
    mean = mean(time, na.rm = TRUE)
  )

## Spiky has undo and domain kb
choice = c("asp2", "asp2-k")
df_1 = subset(df_ck, domain == "spiky-tireworld" & planner %in% choice)
i_1 = df_1[df_1$planner == choice[1],]$instance
i_2 = df_1[df_1$planner == choice[2],]$instance
intersection = intersect(i_1, i_2)
df_1 = subset(df_1, instance %in% intersection)
df_1$planner = factor(df_1$planner, levels = choice)
test = wilcox.test(df_1$time ~ df_1$planner, paired=TRUE)
test
group_by(df_1, domain, planner) %>%
  summarise(
    count = n(),
    median = median(time, na.rm = TRUE),
    #IQR = IQR(time, na.rm = TRUE),
    mean = mean(time, na.rm = TRUE)
  )

## islands has undo
choice = c("asp2", "asp2-u")
df_1 = subset(df_ck, domain == "islands" & planner %in% choice)
i_1 = df_1[df_1$planner == choice[1],]$instance
i_2 = df_1[df_1$planner == choice[2],]$instance
intersection = intersect(i_1, i_2)
df_1 = subset(df_1, instance %in% intersection)
df_1$planner = factor(df_1$planner, levels = choice)
test = wilcox.test(df_1$time ~ df_1$planner, paired=TRUE)
test

## truck has undo
choice = c("asp2", "asp2-u")
df_1 = subset(df_ck, domain == "tireworld-truck" & planner %in% choice)
i_1 = df_1[df_1$planner == choice[1],]$instance
i_2 = df_1[df_1$planner == choice[2],]$instance
intersection = intersect(i_1, i_2)
df_1 = subset(df_1, instance %in% intersection)
df_1$planner = factor(df_1$planner, levels = choice)
test = wilcox.test(df_1$time ~ df_1$planner, paired=TRUE)
test

t.test(df_1[df_1$planner == choice[1],]$time,
       df_1[df_1$planner == choice[2],]$time,
      paired=TRUE)

## first responders has undo

## Blocksworld has undo