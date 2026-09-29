cases <- list(list(c(0,3,3,3,3,3),rep(3,6),.1),list(rep(1,6),rep(2,6),.12),list(rep(0,6),rep(1,6),.03125),list(rep(2,6),rep(3,6),.03125),list(c(0,0,3,3,3,3),rep(3,6),.005),list(c(0,2,3,3,3,3),rep(3,6),.05))
for (i in seq_along(cases)) {
  v<-cases[[i]];x<-array(0L,c(2L,2L,6L))
  for (k in 1:6) {x[1,,k]<-c(v[[2]][k],3-v[[2]][k]);x[2,,k]<-c(v[[1]][k],3-v[[1]][k])}
  p<-mantelhaen.test(x,exact=TRUE,alternative='two.sided')$p.value
  # The uniform 1->2 row is displayed to two decimal places in the protocol.
  if(i==2) stopifnot(round(p,2)==v[[3]]) else stopifnot(abs(p-v[[3]])<1e-12)
  cat(i,format(p,digits=16),'PASS\n')
}
