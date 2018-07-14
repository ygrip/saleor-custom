import Vue from 'vue';
import Flickity from 'flickity';
import swal from 'sweetalert2';

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
  if ($('#custom-home-navigation').length) {
    console.log('rendering-menu');
    renderMenu();
  }

  $(window).on('shown.bs.modal', function() { 
    var panels = $('.menu-infos');
    var panelsButton = $('.dropdown-item-menu');
    

    //Click dropdown
    panelsButton.click(function() {
        //get data-for attribute
        var dataFor = $(this).attr('data-for');
        var idFor = $(dataFor);

        //current button
        var currentButton = $(this);
        idFor.slideToggle(400, function() {
            //Completed slidetoggle
            if(idFor.is(':visible'))
            {
                currentButton.html('<i class="glyphicon glyphicon-chevron-up text-muted"></i>');
            }
            else
            {
                currentButton.html('<i class="glyphicon glyphicon-chevron-down text-muted"></i>');
            }
        })
    });
  });

  $(window).on('hidden.bs.modal', function() { 
    var panelsButton = $('.dropdown-item-menu');

    //Click dropdown
    panelsButton.unbind();
  });
  
  
  if ($('#top-brands').length) {
    console.log('rendering-top-brands');
    var target = "#featured-brand"
    var position = '#top-brands';
    var url = '/render-top-brand/';
    renderSimilarProduct(url, position,target);
  }

  if ($('#recommended_items').length) {
    console.log('rendering-featured-products');
    var position = '#recommended_items';
    var url = '/api/recommendation/hybrid/';
    getFeaturedProducts(url, position);
  }

  if ($('#recommendation-results').length) {
    var loading_element = '#center-loader';
    var position = '#recommendation-results';
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    var url = '/products/recommendation/all/render/';
    console.log(parsed_query);
    renderSearchResults(url, parsed_query, position, loading_element);
    console.log('done processing recommendation product');
  }

  if ($('#categories_list').length) {
    console.log('rendering-catalog-products');
    var target = ".featured-catalog"
    var position = '#categories_list';
    var url = '/render-categories/';
    renderSimilarProduct(url, position,target);
  }

  if ($('#similar-products').length) {
    console.log('rendering-similar-products');
    var st = new Stopwatch();
    st.start();
    var target = "#featured-courses"
    var position = '#similar-products';
    var url = $('#similar-products').data('url');
    var id_product = $('#similar-products').data('id_product');
    
    renderSimilarProduct(url, position,target);
    setTimeout(function (){
      st.stop(); // Stop it 10 seconds later...
      trackItem(id_product);
    }, 10000);
  }

  if ($('#sale-results').length) {
    console.log('rendering-sale-products');
    var loading_element = '#center-loader';
    var position = '#sale-results';
    var url = $('#sale-results').data('url');
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    renderSearchResults(url, parsed_query, position, loading_element);
  }
  
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
  if ($('#similar-results').length) {
    var loading_element = '#center-loader';
    var position = '#similar-results';
    const query = window.location.search.substring(1);
    const parsed_query = parse_query_string(query);
    var url = $('#similar-results').data('url');
    console.log(parsed_query);
    renderSearchResults(url, parsed_query, position, loading_element);
    console.log('done processing similar product');
  }
});

function renderMenu(){
  $.ajax({
      type: 'GET',
      url: '/render-menu/',
      crossDomain: 'true',
      success(response) {
        $('#custom-home-navigation').html(response);
      },
      error (xhr, status) {
      	swal({
		  type: 'error',
		  title: 'Oops...',
		  text: 'Something went wrong! '+status,
		})
      },
  });
}

function trackItem(id_item){
  console.log('tracking item');
  var csrftoken = getCookie('csrftoken');
  $.ajax({
      type: 'POST',
      url: '/api/track/insertvisit/',
      data:{
        product_id: id_item,
        csrfmiddlewaretoken: csrftoken,
      },
      crossDomain: 'true',
      success(response) {
        if(response.success==true){
          swal({
            type: 'success',
            title: 'Great...',
            text: response.message,
          })
        }else{
          swal({
            type: 'warning',
            title: 'Oops...',
            text: response.message,
          })
        }
      },
      error (xhr, status) {
        swal({
          type: 'error',
          title: 'Oops...',
          text: 'Something went wrong! '+status,
        })
      },
  });
}

function renderSimilarProduct(url, position, target){
  $(position).append(spinner_loading);
  $.ajax({
      type: 'GET',
      url: url,
      crossDomain: 'true',
      success(response) {
        $(position).html('');
        $(position).html(response);
        renderRating(position);
        var galleryElems = document.querySelectorAll(target);
        for ( var i=0, len = galleryElems.length; i < len; i++ ) {
          var galleryElem = galleryElems[i];
          new Flickity( galleryElem, {
            // options
            cellSelector: '.course-item',
            cellAlign: 'left',
            lazyLoad: true,
            pageDots: false,
            arrowShape: { 
              x0: 10,
              x1: 70, y1: 50,
              x2: 65, y2: 15,
              x3: 45
            }
          });
          
        }
        $('.flickity-prev-next-button.previous').css('left','-1.5em');
        $('.flickity-prev-next-button.next').css('right','-1.5em');
        $('.flickity-viewport').css('min-height','240px !important');
        $('.flickity-viewport').css('max-height','640px !important');
        $('.flickity-viewport').css('height','320px !important');
      },
      error (xhr, status) {
        $(position).html('');
        swal({
    		  type: 'error',
    		  title: 'Oops...',
    		  text: 'Something went wrong! '+status,
    		})
      },
  });
}

function getFeaturedProducts(url, position){
  $(position).append(spinner_loading);
  $.ajax({
      type: 'GET',
      url: url,
      crossDomain: 'true',
      success(response) {
        console.log(response)
        if(response.success==true){
          var url = '/api/recommendation/partial/render/';
          var newposition = '#recommended_items';
          var data = JSON.stringify(response.recommendation.products);
          var source = response.source;
          var total = response.recommendation.total;
          renderFeaturedProducts(url,newposition,data,source, total);
          if(response.evaluate==true){
            var evaluate_position = '#evaluation';
            var url_eval = '/api/recommendation/evaluate/';
            evaluateRecommendation(url_eval,evaluate_position,data,source,response.process_time);
          }
        }else{
          $(position).html('');
          swal({
            type: 'error',
            title: 'Oops...',
            text: 'Something went wrong! '+status,
          })
        }
      },
      error (xhr, status) {
        $(position).html('');
            swal({
          type: 'error',
          title: 'Oops...',
          text: 'Something went wrong! '+status,
        })
      },
  });
}

function evaluateRecommendation(url,position,products,source,time){
  console.log('evaluating recommendation');
  $(position).append('<h2 class="text-center" id="evaluattion-label" style="width:100%;">Evaluation</h2><hr><div class="row-fluid card" id="evaluation-content"></div>');
  var newposition = '#evaluation-content';
  $(newposition).append(spinner_loading);
  var csrftoken = getCookie('csrftoken');
  $.ajax({
      type: 'POST',
      method:'POST',
      url: url,
      data:{
        recommended:products,
        source:source,
        csrfmiddlewaretoken: csrftoken,
      },
      crossDomain: 'true',
      success(response) {
        console.log(response)
        if(response.success==true){
          $(newposition).html('');

          var results = '<div class="row-fluid card" style="margin: 0 auto; padding:10px;"y><div class="table-responsive"><table class="table table-striped">';
          results += `<tr>
                    <td>data source :</td>
                    <td><strong>`+source+`</strong></td>
                  </tr>`
          for (const [key, value] of Object.entries(response.evaluation)) {
            results += `<tr>
                    <td>`+key+` :</td>
                    <td><strong>`+value+`</strong></td>
                  </tr>`
          }
          results += `<tr>
                    <td>process time :</td>
                    <td><strong>`+time+`</strong></td>
                  </tr>`
          results += `</table>
            </div><div>`

          $(newposition).html(results);
        }else{
          $(position).html('');
        }
      },
      error (xhr, status) {
        $(position).html('');
          swal({
            type: 'error',
            title: 'Oops...',
            text: 'Something went wrong! '+status,
        })
      },
  });
}

function renderFeaturedProducts(url, position, inputdata, source, total){
  var csrftoken = getCookie('csrftoken');
  $.ajax({
      type: 'POST',
      url: url,
      data:{
        products:inputdata,
        source:source,
        csrfmiddlewaretoken: csrftoken,
      },
      crossDomain: 'true',
      success(response) {
        $(position).html('');
        $(position).html(response);

        if(total>16){
          $(position).append(`
            <div class="row-fluid" style="width:100%;">
              <hr>
                <div class="home__block1" style="margin : 0 auto; margin-bottom: 1.5em;"> 
                <a class="btn fancy-button-on col-sm-2" href="products/recommendation/all/" style="width: 100%; height:100%;"> 
                  Show More 
                </a> 
              </div>
              <hr>
            </div>`);
        }
        renderRating(position);

      },
      error (xhr, status) {
        $(position).html('');
            swal({
          type: 'error',
          title: 'Oops...',
          text: 'Something went wrong! '+status,
        })
      },
  });
}

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
	      swal({
  			  type: 'error',
  			  title: 'Oops...',
  			  text: 'Something went wrong! '+status,
  			})
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

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Create a stopwatch "class." 
function Stopwatch(){
  var startTime, endTime, instance = this;

  this.start = function (){
    startTime = new Date();
  };

  this.stop = function (){
    endTime = new Date();
  }

  this.clear = function (){
    startTime = null;
    endTime = null;
  }

  this.getSeconds = function(){
    if (!endTime){
    return 0;
    }
    return Math.round((endTime.getTime() - startTime.getTime()) / 1000);
  }

  this.getMinutes = function(){
    return instance.getSeconds() / 60;
  }      
  this.getHours = function(){
    return instance.getSeconds() / 60 / 60;
  }    
  this.getDays = function(){
    return instance.getHours() / 24;
  }   
}
