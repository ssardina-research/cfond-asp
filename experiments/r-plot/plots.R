####
# R-script to generate multi-figure coverage graphs.
#       Author: Nitin Yadav and Sebastian Sardina for ECAI23 paper
#
# You may want to change the parameters constants below under "CONSTANTS" section.
#
# The script expects a CSV file with the following headers:
#
#       domain: name of the planning domain
#       solver: name of the solver/solver
#       instance_id: id of the planning problem
#       status: 1 if problem was solved, -1 if ran out of time, -2 if ran out of memory and 0 if could not solve for other reasons
#       cputime: cputime take to solve the problem, -1 if the planer ran out of resources
#
#       domain,instance,solver,status,cputime
#       domain_1,p1,PLN_1,1,696.853460246388
#       domain_1,p2,PLN_1,1,937.635542893674
#       domain_1,p3,PLN_1,1,859.808497063841
#       domain_1,p4,PLN_1,1,956.171513837123
#       domain_1,p5,PLN_1,1,940.861330914696
#       domain_1,p6,PLN_1,1,987.698655947538
#       domain_1,p7,PLN_1,1,1035.17954074212
#       domain_1,p8,PLN_1,1,950.456002157257
#       domain_1,p9,PLN_1,1,797.099476990923
#       domain_1,p10,PLN_1,1,874.812547986277
####

######################################
#### import the required libraries for plotting
######################################
library(ggplot2)
library(dplyr)

main_file = "data/results"
main_file = "data/cfond_benchexec_stats"

#### SET YOUR CONSTANTS
csv_file = paste(main_file, ".csv", sep="")
output_pdf = paste(main_file, ".pdf", sep="")
output_png = paste(main_file, ".png", sep="")

plot_width = 15
plot_height = 12
plot_dpi = 300

######################################

# read the csv
df = read.csv(csv_file)

# set solver and domain as categories
df$solver = factor(df$solver, levels = sort(unique(df$solver)))
df$domain = factor(df$domain, levels = sort(unique(df$domain)))

# compute the coverage by grouping by domain and solver, and then computing the mean
###
# The Benchexec script uses the following notation
# { "true": 1, "false": 0, "True": 1, "False": 0, False: 0, True: 1, "OUT OF MEMORY (false)": -2, "TIMEOUT (false)": -1, "TIMEOUT (true)": 1 }
# 
# We need to use 1 for solved, and 0 for not solved
###
df <- df %>% mutate(solved_int = ifelse(status == 1, 1, 0))
df_c = df %>%
  group_by(domain, solver) %>%
  summarise(coverage = mean(solved_int))

# scale the y coordinate slightly to show clearly on plots
span_coverage = max(df$cputime)*0.95
df_c$coverage_x = span_coverage*0.5 *(1 + df_c$coverage)

# create a coverage label
df_c$coverage_label = paste(round(df_c$coverage*100, 2), "%", sep="")


## compute the average cputime for the solved instances
df_means = df %>%
  filter(status==1) %>%
  group_by(domain, solver) %>%
  summarise(mean_time = mean(cputime))

# create a label by rounding to 1 decimal place
df_means$mean_label = round(df_means$mean_time,1)

# convert category to number so that we can move them vertically in plot
df_means$p_y = as.numeric(df_means$solver)

# build basic plot  with time x and planer y axes
df_solved = df[df$solved_int==1,]
p = ggplot(df_solved, aes(cputime, solver))

# add time scatter plot per solver, with bar
p = p + geom_segment(aes(x=0, xend=coverage_x, y = solver, yend = solver), data=df_c, color="grey50") + 
  geom_point(size=2,aes(colour = solver, shape=solver),show.legend = FALSE) + 
  scale_shape_manual(values=seq(0,15))

# add coverage number text in rounded box with % at the end of the bar
p = p + geom_label(aes(x=coverage_x, y=solver, label=coverage_label), data=df_c, size=3)

# add mean time vertical mark and number per solver
p = p + geom_segment(aes(x=mean_time, xend=mean_time, y = p_y-0.2, yend=p_y+0.2), data=df_means, linewidth=0.8, color="grey30")
p = p + geom_text(aes(x=mean_time+100, y=p_y+0.2, label=mean_label), data=df_means, size=3)

# add the facet subplots for each domain
p = p + facet_wrap(~domain, ncol=4,strip.position="right") #facet_grid(cols = vars(domain))

# add labels text
p + scale_y_discrete(limits=rev) + xlab("Time (sec)") + ylab("solvers")


# finally, save the plot in PDF and PNG formats (https://ggplot2.tidyverse.org/reference/ggsave.html)
ggsave(output_pdf, width=plot_width, height=plot_height, units="in", dpi=plot_dpi)
ggsave(output_png, width=plot_width, height=plot_height, units="in", dpi=plot_dpi)
