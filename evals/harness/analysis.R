# Frozen primary analysis. Input is a post-unblinding 144-row CSV, never model output text.
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) stop('usage: Rscript analysis.R scores.csv output-directory')
d <- read.csv(args[1], stringsAsFactors=FALSE)
settings <- c('fable-high','opus-medium','sonnet-medium','sonnet-low')
cases <- c('accent-only','diagnose-staging','helper-unavailable','ideas-only','neighbour-bug','override-present')
stopifnot(nrow(d)==144L, !anyDuplicated(d$session_id), !anyNA(d), all(d$completion %in% c(0,1)), setequal(d$setting,settings), setequal(d$case,cases), setequal(d$arm,c('baseline','candidate')))
out <- args[2]
if (dir.exists(out)) stop('Refuse to overwrite analysis')
dir.create(out,recursive=TRUE)
results <- list(); strata <- list()
for (setting in settings) {
  x <- array(0L,c(2L,2L,6L),dimnames=list(arm=c('candidate','baseline'),outcome=c('complete','incomplete'),case=cases))
  for (i in seq_along(cases)) for (arm in c('candidate','baseline')) {
    rows <- subset(d, d$setting==setting & d$case==cases[i] & d$arm==arm)
    stopifnot(nrow(rows)==3L)
    x[arm,,i] <- c(sum(rows$completion),3L-sum(rows$completion))
  }
  fit <- tryCatch(mantelhaen.test(x,exact=TRUE,alternative='two.sided'),error=function(e) e)
  estimable <- !inherits(fit,'error') && is.finite(fit$p.value)
  p <- if (estimable) fit$p.value else 1
  baseline <- sum(x['baseline','complete',]); candidate <- sum(x['candidate','complete',])
  results[[setting]] <- data.frame(setting=setting,baseline=baseline,candidate=candidate,n_per_arm=18L,common_odds_ratio=if(estimable)unname(fit$estimate) else NA_real_,ci_lower=if(estimable)fit$conf.int[1] else NA_real_,ci_upper=if(estimable)fit$conf.int[2] else NA_real_,exact_p=p,estimable=estimable,regression_only=baseline>=14L,improvement=estimable && baseline<14L && candidate>baseline && p<0.05)
  strata[[setting]] <- transform(as.data.frame.table(x,responseName='count'),setting=setting)
}
r <- do.call(rbind,results)
r$holm_p <- p.adjust(r$exact_p,method='holm')
r$headline_eligible <- r$improvement & r$holm_p<0.05
write.csv(r,file.path(out,'settings.csv'),row.names=FALSE)
write.csv(do.call(rbind,strata),file.path(out,'strata.csv'),row.names=FALSE)
writeLines(c(R.version.string,paste('stats',as.character(packageVersion('stats'))),capture.output(sessionInfo())),file.path(out,'versions.txt'))
