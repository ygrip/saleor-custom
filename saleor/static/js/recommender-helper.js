import Vue from 'vue';

console.log('recommender helper loaded');

$(document).ready(() => {

  if ($('#query-results').length) {
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    const url = '/search/render/'
    console.log(parsed_query);
    renderSearchResults(url, parsed_query);
    console.log('done processing query');
  }
});

function renderSearchResults(url, query) {
  $('#center-loader').css('display', 'inline-block');
  $('.animationload').css('display', 'block');
  	console.log(query);
  	const page = 'page' in query ? query.page : 1
  	const query_string = query.q.replace(/\+/g, '%20');
  	const clean_query = decodeURIComponent(query_string);
  	$.ajax({
	    type: 'GET',
	    url: url,
	    data: {
	    	q: clean_query,
	    	page: page,
	    },
	    crossDomain: 'true',
	    success(response) {
	      $('#center-loader').css('display', 'none');
	      $('.animationload').css('display', 'none');
	      $('#query-results').html(response);
	      renderRating('#query-results');
	    },
	    error (xhr, status) {
	      $('#center-loader').css('display', 'none');
	      $('.animationload').css('display', 'none');
	      alert(`Unknown error ${status}`);
	    },
  });
}

function renderRating(element) {
  new Vue({
    el: element,
    methods: {
      setRating(rating) {
		      this.rating = `you have selected ${rating}`;
		      console.log(this.rating);
		    },
		    showCurrentRating(rating) {
		      this.currentRating = (rating === 0) ? this.currentSelectedRating : rating;
		    },
		    setCurrentSelectedRating(rating) {
		      this.currentSelectedRating = rating;
		      console.log(`selected ${rating}`);
		    },
    },
    data: {
		    rating: '',
		    currentRating: '',
		    currentSelectedRating: '',
		    boundRating: 5,
    },
  });
  $('.vue-star-rating div').each(function(index) {
    	$(this).css('margin', '0 auto');
  });
}

function parse_query_string(query) {
  var vars = query.split("&");
  var query_string = {};
  for (var i = 0; i < vars.length; i++) {
    var pair = vars[i].split("=");
    var key = decodeURIComponent(pair[0]);
    var value = decodeURIComponent(pair[1]);
    // If first entry with this name
    if (typeof query_string[key] === "undefined") {
      query_string[key] = decodeURIComponent(value);
      // If second entry with this name
    } else if (typeof query_string[key] === "string") {
      var arr = [query_string[key], decodeURIComponent(value)];
      query_string[key] = arr;
      // If third or later entry with this name
    } else {
      query_string[key].push(decodeURIComponent(value));
    }
  }
  return query_string;
}