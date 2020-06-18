
function handicapper(p1=null,p2=null,mode='h2h') {

	if (p1 != null) { 
		p1 = p1.replace('(','\\\\(').replace(')','\\\\)')
		console.log('p1 is ',p1)
	}
	if (p2 != null) { 
		p2 = p2.replace('(','\\\\(').replace(')','\\\\)')
	}
	


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
AH = (p1f-p1a)/p1m-(p2f-p2a)/p2m;
if (mode=='h2h'){AH/=2};
AH = Math.round(AH*100)/100;
avetot = ((p1f+p1a)/p1m+(p2f+p2a)/p2m)/2;
avetot = Math.round(avetot*100)/100;	

return {'AH':AH,'avetot':avetot, 'p1m':p1m,'p2m':p2m,'p1f':p1f,'p1a':p1a,'p2f':p2f,'p2a':p2a};
}

function h2h(tr) {

	num_selected = $('.h2hsel').length


  //if it has the class, toggle off
  if ( $(tr).hasClass('h2hsel') ) {$(tr).toggleClass('h2hsel')} else {

  	if (num_selected < 2) {
  		$(tr).toggleClass('h2hsel')
  }
  }

selected = $('.h2hsel')
num_selected = selected.length
if (num_selected == 2) {
	p1 = $(selected[0])[0].children[0].textContent
	p2 = $(selected[1])[0].children[0].textContent
	console.log(p1,p2);
	console.log(handicapper(p1,p2));
	$('#h2hdata').html(p1+' '+p2);
	$('#h2hdata').show();

} else {
	$('#h2hdata').hide()

}
}