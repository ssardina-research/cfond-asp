library(ggplot2)
library(dplyr)
library(tikzDevice)

planners = c("paladinus-4h", "minisat-4h", "glucose-4h", "prp-4h", "asp1", "asp2")
setwd("~/Work/Software/fond-compact-asp/benchmarking/analysis")
df = read.csv("./solved_results.csv")
df_c = read.csv("./coverage.csv")

domain_levels = c("islands", "spiky-tireworld", "tireworld-truck", "miner", "doors", "acrobatics", "blocksworld", "earth_observation",
                  "beam-walk", "chain-of-rooms", "elevators", "faults-ipc08","first-responders-ipc08","tireworld","triangle-tireworld", "zenotravel")

domain_labels = c("Islands (60)", "Spiky Tireworld (11)", "Tireworld Truck (74)", "Miner (50)", "Doors (15)", "Acrobatics (8)", "Blocksworld (70)", "Earth Observation (40)",
                  "Beam Walk (11)", "Chain of Rooms (10)", "Elevators (15)", "Faults (55)","First Responders (73)","Tireworld (11)","Triangle Tireworld (40)", "zenotravel (15)")
planner_levels = c("CASP1", "CASP2", "FSGLU", "FSMST", "PALAD", "PRP")

df = subset(df, planner %in% planners)
#df = subset(df, domain != "tireworld")
df$planner[df$planner == 'paladinus-4h'] = "PALAD"
df$planner[df$planner == 'prp-4h'] = "PRP"
df$planner[df$planner == 'glucose-4h'] = 'FSGLU'
df$planner[df$planner == 'minisat-4h'] = 'FSMST'
df$planner[df$planner == 'asp1'] = 'CASP1'
df$planner[df$planner == 'asp2'] = 'CASP2'
df$plannerg <- factor(df$planner, levels = planner_levels)
df$domain = factor(df$domain, levels=domain_levels, labels=domain_labels)

df_c = subset(df_c, planner %in% planners)
#df_c = subset(df_c, domain != "tireworld")
df_c$planner[df_c$planner == 'paladinus-4h'] = "PALAD"
df_c$planner[df_c$planner == 'prp-4h'] = "PRP"
df_c$planner[df_c$planner == 'glucose-4h'] = 'FSGLU'
df_c$planner[df_c$planner == 'minisat-4h'] = 'FSMST'
df_c$planner[df_c$planner == 'asp1'] = 'CASP1'
df_c$planner[df_c$planner == 'asp2'] = 'CASP2'
df_c$plannerg = factor(df_c$planner, levels = planner_levels)
df_c$coverage_y = df_c$coverage*125
df_c$coverage_label = paste(df_c$coverage, "%", sep="")
df_c$domain = factor(df_c$domain,levels=domain_levels, labels=domain_labels)

## means
aggregate(df$time, list(df$planner, df$domain), FUN=mean)
df_means = df %>% group_by(domain, planner) %>% summarise_at(vars(time), list(mean=mean))
df_means$mean = as.numeric(df_means$mean)
df_means$domain = factor(df_means$domain,levels=domain_labels, labels=domain_labels)
df_means$planner = factor(df_means$planner, levels =planner_levels)
df_means$p_y = 7 - as.numeric(df_means$planner)
df_means$mean_label = round(df_means$mean,1)

p = ggplot(df, aes(time, planner))
p = p + geom_segment(aes(x=0, xend=coverage_y, y = planner, yend = planner), data=df_c, color="grey50") + geom_point(size=2,aes(colour = planner, shape=planner),show.legend = FALSE)
p = p + geom_segment(aes(x=mean, xend=mean, y = p_y-0.2, yend=p_y+0.2), data=df_means, linewidth=0.8, color="grey30") 
p = p + geom_label(aes(x=coverage_y+1000, y=planner, label=coverage_label), data=df_c, size=3)
p = p + geom_text(aes(x=mean+500, y=p_y+0.35, label=mean_label), data=df_means, size=3)
p = p + facet_wrap(~domain, ncol=4,strip.position="right") #facet_grid(cols = vars(domain))
p + scale_y_discrete(limits=rev) + xlab("Time (sec)") + ylab("Planners") 

#tikz('results_fig.tex', width = 7, height=3)
#print(p)
#dev.off()

ggsave("main_results_reg.pdf", width=14, height=7, units="in", dpi=300)

## STAT TESTS
df_p = read.csv("./solved_results.csv")

## Islands
choice = c("asp1", "asp2", "minisat-4h")
df_1 = subset(df_p, domain == "islands" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)

# Truck
choice = c("asp1", "asp2", "glucose-4h")
df_1 = subset(df_p, domain == "tireworld-truck" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)

# Miner
choice = c("asp1", "asp2", "glucose-4h", "minisat-4h")
df_1 = subset(df_p, domain == "miner" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)

# Doors
choice = c("prp-4h", "asp2", "glucose-4h")
df_1 = subset(df_p, domain == "doors" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)


# Acrobatics
choice = c("prp-4h", "paladinus-4h")
df_1 = subset(df_p, domain == "acrobatics" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)


# Tireworld
choice = c("prp-4h", "paladinus-4h", "glucose-4h", "minisat-4h")
df_1 = subset(df_p, domain == "tireworld" & planner %in% choice)
compare_means(time ~ planner, df_1, method = "wilcox.test", paired = TRUE)
