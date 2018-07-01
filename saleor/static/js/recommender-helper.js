import Vue from 'vue';

console.log('recommender helper loaded');
const processing_label = ` <div class="col-12 justify-content-between align-items-center mb-4 mb-md-0 menu" style="margin-top: -200px; margin-bottom: 10em !important; text-align: center; border-bottom: 1px solid #D3D1D0;">
                            <h2>Processing your request</h2>
                          </div>
                          <br>
                          <br> `;
const spinner_loading = ` <div class="spinner">
                          <div class="rect1"></div>
                          <div class="rect2"></div>
                          <div class="rect3"></div>
                          <div class="rect4"></div>
                          <div class="rect5"></div>
                        </div> `;
const fold_loading = ` <div class="sk-folding-cube" style="margin: 0 auto;">
                        <div class="sk-cube1 sk-cube"></div>
                        <div class="sk-cube2 sk-cube"></div>
                        <div class="sk-cube4 sk-cube"></div>
                        <div class="sk-cube3 sk-cube"></div>
                      </div> `;
const fancy_loading = ` <div class="animationload">
                          <div class="osahanloading"></div>
                      </div> `;
$(document).ready(() => {

  
  if ($('#query-results').length) {
    var loading_element = '#center-loader';
    var position = '#query-results';
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    const url = '/search/render/'
    console.log(parsed_query);
    renderSearchResults(url, parsed_query, position, loading_element);
    console.log('done processing query');
  }
  if ($('#tags-results').length) {
    var loading_element = '#center-loader';
    var position = '#tags-results';
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    const url = '/products/tags/render/' ;
    console.log(parsed_query);
    renderSearchResults(url, parsed_query, position, loading_element);
    console.log('done processing tags');
  }
});

function renderSearchResults(url, query, position, loading_element) {
    $(loading_element).css('display','inline-block');
    $(loading_element).append(fancy_loading);
  	console.log(query);
  	const page = 'page' in query ? query.page : 1;
  	const query_string = 'q' in query ? query.q.replace(/\+/g, '%20') : '';
  	const clean_query = 'q' in query ? decodeURIComponent(query_string) : '';
  	$.ajax({
	    type: 'GET',
	    url: url,
	    data: {
	    	q: clean_query,
	    	page: page,
	    },
	    crossDomain: 'true',
	    success(response) {
        $(loading_element).css('display','none');
	      $(loading_element+' div:last-child').remove();
	      $(position).html(response);
	      renderRating(position);
	    },
	    error (xhr, status) {
        $(loading_element).css('display','none'); 
	      $(loading_element+' div:last-child').remove(); 
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