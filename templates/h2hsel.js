
function handicapper(p1=null,p2=null,mode='h2h') {

	var p1f = 0;
	var p1a = 0;
	var p1m = 0;
	var p2f = 0;
	var p2a = 0;
	var p2m = 0;

	//get all games, either the total, or h2h subset
	if (mode!='h2h') {
		fil = $('#gamestable > tbody > tr')
	}
	else {

		fil = $('#gamestable > tbody > tr:contains('+p1+'):contains('+p2+')') }

	//filter to force exact string match rather than loosely contains
	fil2 = fil.filter(function () { 

		if ($(this)[0].children.length == 5) {

			row = $(this)[0].children
			home = row[1].textContent;
			away = row[2].textContent;
			homescr = parseInt(row[3].textContent);
			awayscr = parseInt(row[4].textContent);

	//do not return anything unless scores exist
	if (!Number.isInteger(homescr) || !Number.isInteger(awayscr)) { return null}

		if (mode=='h2h') {
			//case where only h2h games are requested
			if (home == p1 && away == p2 ) {
				p1f += homescr
				p2f += awayscr
				p1a += awayscr
				p2a += homescr
				p1m += 1
				p2m += 1
			}

			if (home == p2 && away == p1  ) {
				p1f += awayscr
				p2f += homescr
				p1a += homescr
				p2a += awayscr
				p1m += 1
				p2m += 1
			}
		} else {
			//case where mode is all games
			if (home == p1) {
				p1f += homescr
				p1a += awayscr
				p1m += 1
			}
			if (home == p2) {
				p2f += homescr
				p2a += awayscr
				p2m += 1
			}
			if (away == p1) {
				p1f += awayscr
				p1a += homescr
				p1m += 1
			}
			if (away == p2) {
				p2f += awayscr
				p2a += homescr
				p2m += 1
			}

		}

	}
}
)	

//work out the average handicap and total
if (mode=='h2h') {
	AH = Math.round((p1f-p1a)/p1m*100)/100;
	avetot = Math.round((p1f+p2f)/p1m*100)/100;
}
else {
	AH = (p1f-p1a)/p1m-(p2f-p2a)/p2m;
	AH = Math.round(AH*100)/100;
	avetot = ((p1f+p1a)/p1m+(p2f+p2a)/p2m)/2;
	avetot = Math.round(avetot*100)/100;	
}

	return {'AH':AH,'avetot':avetot, 'p1m':p1m,'p2m':p2m,'p1f':p1f,'p1a':p1a,'p2f':p2f,'p2a':p2a};
}