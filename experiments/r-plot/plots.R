####
# Plotting example. The script expects a csv file with the following headers:
# domain: name of the planning domain
# planner: name of the planner/solver
# instance_id: id of the planning problem
# solved: 1 if problem was solved, 0 otherwise
# time: time take to solve the problem, -1 if the planer ran out of resources
####

# import the required libraries for plotting
library(ggplot2)
library(dplyr)

# read the csv
df = read.csv("./results.csv")

# set planner and domain as categories
df$planner = factor(df$planner, levels = sort(unique(df$planner)))
df$domain = factor(df$domain, levels = sort(unique(df$domain)))

# compute the coverage by grouping by domain and planner, and then computing the mean
df_c = df %>%
        group_by(domain, planner) %>%
        summarise(coverage = mean(solved))

# scale the y coordinate slightly to show clearly on plots
df_c$coverage_y = df_c$coverage*125

# create a coverage label
df_c$coverage_label = paste(round(df_c$coverage*100, 2), "%", sep="")


## compute the average time for the solved instances
df_means = df %>%
          filter(solved==1) %>%
          group_by(domain, planner) %>%
          summarise(mean_time = mean(time))

# create a label by rounding to 1 decimal place
df_means$mean_label = round(df_means$mean_time,1)

# convert category to number so that we can move them vertically in plot
df_means$p_y = as.numeric(df_means$planner)

p = ggplot(df, aes(time, planner))
p = p + geom_segment(aes(x=0, xend=coverage_y, y = planner, yend = planner), data=df_c, color="grey50") + geom_point(size=2,aes(colour = planner, shape=planner),show.legend = FALSE)
p = p + geom_segment(aes(x=mean_time, xend=mean_time, y = p_y-0.2, yend=p_y+0.2), data=df_means, linewidth=0.8, color="grey30")
p = p + geom_label(aes(x=coverage_y+1000, y=planner, label=coverage_label), data=df_c, size=3)
p = p + geom_text(aes(x=mean_time+100, y=p_y+0.2, label=mean_label), data=df_means, size=3)
p = p + facet_wrap(~domain, ncol=4,strip.position="right") #facet_grid(cols = vars(domain))
p + scale_y_discrete(limits=rev) + xlab("Time (sec)") + ylab("Planners")

ggsave("results.pdf", width=15, height=12, units="in", dpi=300)

