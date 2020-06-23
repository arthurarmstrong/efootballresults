
function handicapper(p1=null,p2=null,mode='h2h') {

	if (p1 != null) { 
		p1 = p1.replace('(','\\\\(').replace(')','\\\\)')
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
	var p1w = 0;
	var p1d = 0;
	var p1l = 0;
	var p2w = 0;
	var p2d = 0;
	var p2l = 0;
	var p1fa = []
	var p2fa = []

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
				p1fa[p1fa.length] = homescr - awayscr
				p2fa[p2fa.length] = awayscr - homescr

				if (homescr > awayscr) { p1w+=1; p2l+=1;} else if ( homescr == awayscr ) {p1d += 1; p2d += 1;} else if (awayscr > homescr) { p2w += 1; p1l += 1;}
			}

			if (home == p2 && away == p1  ) {
				p1f += awayscr
				p2f += homescr
				p1a += homescr
				p2a += awayscr
				p1m += 1
				p2m += 1
				p2fa[p2fa.length] = homescr - awayscr
				p1fa[p1fa.length] = awayscr - homescr

				if (homescr > awayscr) { p2w+=1; p1l+=1;} else if ( homescr == awayscr ) {p1d += 1; p2d += 1;} else if (awayscr > homescr) { p1w += 1; p2l += 1;}
			}
		} else {
			//case where mode is all games
			if (home == p1) {
				p1f += homescr
				p1a += awayscr
				p1m += 1
				p1fa[p1fa.length] = homescr - awayscr

				if (homescr > awayscr) { p1w+=1} else if ( homescr == awayscr ) {p1d += 1;} else if (awayscr > homescr) {p1l += 1;}
			}
			if (home == p2) {
				p2f += homescr
				p2a += awayscr
				p2m += 1
				p1fa[p1fa.length] = awayscr - homescr

				if (homescr > awayscr) { p2w+=1} else if ( homescr == awayscr ) {p2d += 1;} else if (awayscr > homescr) {p2l += 1;}
			}
			if (away == p1) {
				p1f += awayscr
				p1a += homescr
				p1m += 1
				p2fa[p2fa.length] = awayscr - homescr

				if (awayscr > homescr) { p1w+=1} else if ( homescr == awayscr ) {p1d += 1;} else if (homescr > awayscr) {p1l += 1;}
			}
			if (away == p2) {
				p2f += awayscr
				p2a += homescr
				p2m += 1
				p2fa[p2fa.length] = homescr - awayscr

				if (awayscr > homescr) { p2w+=1} else if ( homescr == awayscr ) {p2d += 1;} else if (homescr > awayscr) {p2l += 1;}
			}

		}

	}
}
)	

//work out the average handicap and total
AH = (p1f-p1a)/p1m-(p2f-p2a)/p2m;
p1medfa = median(p1fa)
p2medfa = median(p2fa)
console.log('p1medfa',p1medfa,'p2medfa',p2medfa)
//AH = (AH + p1medfa-p2medfa)/2
if (mode=='h2h'){AH/=2};
AH = Math.round(AH*100)/100;

avetot = ((p1f+p1a)/p1m+(p2f+p2a)/p2m)/2;
avetot = Math.round(avetot*100)/100;	

return {'AH':AH,'avetot':avetot, 'p1m':p1m,'p2m':p2m,'p1f':p1f,'p1a':p1a,'p2f':p2f,'p2a':p2a,'p1w':p1w,'p1d':p1d,'p1l':p1l,'p2w':p2w,'p2d':p2d,'p2l':p2l,'mode':mode,'p1medfa':p1medfa,'p2medfa':p2medfa};
}

function h2h(tr) {

num_selected = $('.h2hsel').length


  //if it has the class, toggle off
  if ( $(tr).hasClass('h2hsel') ) {
  	$('.h2hsel').removeAttr('data-toggle');
  	$('.h2hsel').removeAttr('data-html');
  	$('.h2hsel').removeAttr('data-original-title');
  	$('.h2hsel').removeAttr('title');
  	$('.h2hsel > th').removeAttr('onmouseover');

  	$(tr).toggleClass('h2hsel');
  } else {

  		$(tr).toggleClass('h2hsel')
  		//$('.h2hsel > th').filter(function () { $(this).attr('onmouseover','toolTipTable()')})
  }

  

  selected = $('.h2hsel')
  num_selected = selected.length
  if (num_selected == 2) {
  	p1 = $(selected[0])[0].children[0].textContent
  	p2 = $(selected[1])[0].children[0].textContent

  	h2hdata = handicapper(p1,p2);

  	updateH2HStats(h2hdata,p1,p2,selected);

}	else {
	$('tr').removeAttr('title')
	$('tr').removeAttr('data-original-title'); 
}

if (num_selected == 0) {$('#compare_selected').hide()} else {$('#compare_selected').show()}

}

function toolTipTable() {

	//get a table of the subcomp requested
  	resp = getgames(true);
	
	$('#subgroupdialog').first('.modaloverwrite').css('background-color','white');
	$('#subgroupdialog').click(function () {$('#subgroupdialog').modal('hide')});
	$('#subgroupdialog').modal('show');

			
}

function updateH2HStats(h2h,p1,p2,sel) {

	price = prettifyAH(h2h['AH'])
	AH = price[0]
	price = price[1]

	if (h2h['AH'] > 0) {fav = p1} else {fav = p2}

		if (AH < 0) { pm = '+'} else if (AH > 0) { pm = '-' } else { pm = ''}

			if (h2h['p1m'] >= 0 && h2h['p2m']) {
				tooltip = `${p1} and ${p2} have played ${h2h['p1m']} times in the requested timeframe.<p>

				<p>The W/D/L record for ${p1} is ${h2h['p1w']}/${h2h['p1d']}/${h2h['p1l']}.<p>

				${fav}'s average winning margin is ${Math.abs(h2h['AH'])} goals.<p>				

				<p>The average total is ${h2h['avetot']}.<p>

				Suggested AH: ${p1} ${pm}${Math.abs(AH)} at ${price}.`

			} else {
				tooltip = `${p1} and ${p2} have not played each other in the timeframe requested.`;
			}

			$('.h2hsel').attr('data-toggle','tooltip');
			$('.h2hsel').attr('data-html','true');
			$('.h2hsel').attr('data-original-title',tooltip)
			$(function () {
				$('[data-toggle="tooltip"]').tooltip()
			})

		}

		function prettifyAH(AH) {

			mod = AH % 0.25;
			if (mod < 0) { pm = -1 } else { pm = 1 }

				root = Math.round((AH - mod)*100)/100;
				price = '$1.90'

			mod = Math.abs(mod);
			if (mod  > 0.25/5 * 1 ) {price='$1.85'}
				if (mod  > 0.25/5 * 2 ) {price='$1.80'}
					if (mod  > 0.25/5 * 3 ) {root += 0.25*pm;price='$2.00'}
				if (mod  > 0.25/5 * 4 ) {price='$1.95'}

					return [root,price]

			}

		function getPlayerStats(p1) {

			a = $('#ladder > table > tbody > tr').filter(function () { if ($(this).context.children[0].textContent == p1) { 

				row = $(this).context.children
				tds = new Array()
				var i = 0

				for (i == 0 ; i<row.length ; i++) {

					tds[i] = row[i].textContent

				}

			}

		})

		return {'p':tds[0],'mp':tds[1],'W':tds[2],'D':tds[3],'L':tds[4],'F':tds[5],'A':tds[6],'pm':tds[7],'GD':tds[9],'winperc':tds[10],'rating':tds[11]}

		}

function ahBetaSmooth() {
	/*
	a is a parameter that weights how much of the player's overall form to use
	It should be an integer that forces their overall form to decay - specifically it is the number of games
	after which the form has a percentage weighting of 1/e
	b is a similar parameter when there is no existing form.
	*/
	a = 3
	b = 10

	players = getPlayers();


}

function getPlayers() {
	players = []

	$('#ladder > table > tbody > tr').filter(function () {
		players[players.length] = $(this)[0].children[0].textContent

	})

	return players
}

function getAveScore() {

	players = getPlayers();
	total = 0
	count = 0

	var i = 0

	for (i == 0 ; i < players.length ; i++) {

		stats = getPlayerStats(players[i])
		if (!Number.isNaN(parseInt(stats['mp'])) && stats['mp'] > 0) {
			total += Number(stats['F'])/Number(stats['mp'])
			count += 1
	}
	}

	//get the average
	return total/i


}

const median = arr => {
  const mid = Math.floor(arr.length / 2),
    nums = [...arr].sort((a, b) => a - b);
  return arr.length % 2 !== 0 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
};

function clearSelected() {

	$('.h2hsel').removeClass('h2hsel');
	$('#compare_selected').hide();

}