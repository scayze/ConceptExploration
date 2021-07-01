/*
This file provides the frontend functionality of the visualization.
*/

//These variables denote the current state of the website, and are used for various searchqueries
var current_term = "climate change"
var current_detail = "climate change"
var current_date_from = "2001-01"
var current_date_to = "2001-10"
var current_column
var last_starglyph_query
var current_data = {}

//All LeaderLine connections between different nodes
var lines = []
//The Nodes the user decided to delete.
var deleted_nodes = []

//Request an initial animation frame when the user first visits the size
window.requestAnimationFrame(redraw_lines);


$(function() {
    //Initialize the colormap, loading the image
    Color2D.setColormap(Color2D.colormaps.ZIEGLER, function() {}); 
    
    //On clicking the submit button after putting in settings
    $('#submit').bind('click', function() {
        //Disable the submit button until query is responded to
        $('#submit').addClass('disabled');
        //Query the server with the values put in the form fields
        $.getJSON('/_search_term', {
            term: $('#searchterm').val(),
            interval: $('#interval_dropdown').val(),
            from: $('#datefrom').val(),
            to: $('#dateto').val(),
            count: $('#resultcount').val(),
            deep: 1, //HACK: Int instead of bool, bool is bugged
        }, function(data) {
            $('#submit').removeClass('disabled');
            if("message" in data) { //Little hacky way to check if the request failed
                //Show a toast displaying the error
                Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_RIGHT);
                Toast.create("Error: Invalid Searchterm", "The searchterm: " + data["message"] + " does not exist.",TOAST_STATUS.DANGER, 5000);
                return
            }
            console.log(data)
            //Update the graph with the response
            updateGraph(data.result)
        });
        return false;
    });

    //On clicking the submit button in the detail view, after putting in custom starglyph terms
    $('#glyph-submit').bind('click', function() {
        //Disable the submit button until query is responded to
        $('#glyph-submit').addClass('disabled');
        //Query the server with the values put in the form fields
        $.getJSON('/_search_custom_glyph', {
            term: current_detail,
            glyph_terms: $('#glyphterms').val(),
            from: current_date_from,
            to: current_date_to,
        }, function(data) {
            $('#glyph-submit').removeClass('disabled');
            if("message" in data) { //Little hacky way to check if the request failed
                //Show a toast displaying the error
                Toast.setPlacement(TOAST_PLACEMENT.BOTTOM_RIGHT);
                Toast.create("Error: Invalid Searchterms", "The searchterm: " + data["message"] + " does not exist.",TOAST_STATUS.DANGER, 5000);
                return
            }
            //Update the starglpyh, with the color it already has
            color = d3.select("#detail-glyph-circle").style("stroke")
            updateStarglyph(data.result,color)
            
        });
        return false;
    });
    
    //On going to the concordance tab
    $('#concordance-tab').bind('click', function() {
        var table_body = d3.select("#concordance_table")
        d3.select("#detail-footer").style("display","none")
        //Clear the previous concordance
        table_body.selectAll("*").remove()
        //Query the server with the values put in the form fields
        $.getJSON('/_get_concordance', {
        term: current_term,
        word: current_detail,
        from: current_date_from,
        to: current_date_to,
        }, function(data) {
            //Update the concordance view
            updateConcordance(data.result)
        });
        return false;
    });
    //On going to the concordance tab
    $('#starglyph-tab').bind('click', function() {
        d3.select("#detail-footer").style("display","block")
    });
});

//HACK: This is called every frame to redraw the lines at their correct position. 
//Otherwise, the lines wouldnt show correct when scrolling horizontally
//This has a strong performance impact. TODO: Find a better method
function redraw_lines() {
    for(l of lines) {
        l.position()
    }
    window.requestAnimationFrame(redraw_lines);
}

//Function that is called when the starglyph tab is opened in the detail tab
function updateStarglyph(data,color) {
    console.log(data)
    last_starglyph_query = data
    var tab = d3.select("#starglpyh-div")
    tab.selectAll("*").remove()
    create_glyph_circle(tab,data,color)
}

//This function takes the data returned from the concordance search query, and fills the table with data.
function updateConcordance(data) {
    var table_body = d3.select("#concordance_table")

    for(let occurance of data) {
        var tr = table_body.append("tr")
        tr.append("td")
            .attr("class","table-align-right")
            .text(occurance.left)
        tr.append("td")
            .attr("class","table-align-center")
            .html("<p style=\"color:#FF0000\";>" + occurance.kwiq + "</p>")
        tr.append("td")
            .attr("class","table-align-left")
            .text(occurance.right)
        tr.append("td")
            .attr("class","table-align-center")
            .append("button")
            .attr("class","btn btn-secondary")
            .attr("type","button")
            .attr("id","info")
            .text("!")
            .on("click", function() {
                openLink(occurance.url)
            })
    }
}

//This function maps a 2d word embedding to a color on the colorscheme of Zeigler et al.
function position_to_color(pos2d) {
    //Clamp values to bettter fit data in colormap, creating more varied colors
    var xrange = [-0.4,0.7]
    var yrange = [-0.5,0.5]
    pos_x = Math.max( xrange[0], Math.min(pos2d[0], xrange[1]))
    pos_y = Math.max( yrange[0], Math.min(pos2d[1], yrange[1]))
    Color2D.ranges = {x: xrange, y: yrange}; 
    var rgb = Color2D.getColor(pos_x, pos_y)
    //Convert color to css color value
    var formatted_color = "rgb(" + rgb[0].toString() + ", " + rgb[1].toString() + ", " + rgb[2].toString() + ")" 
    return formatted_color
}

//This is the main function of the visualization that generates the visualization, once a query has been processed.
//TODO: This function has gotten to long, split it up into smaller ones.
function updateGraph(data) {
    //Log the query result for debugging purposes
    console.log(data)

    //Get interval and searchterm data from the inputs
    interval = d3.select("#graph")
    searchterm = d3.select("#searchterm").property("value")
    
    //Reset the contents of the graph
    var graph = d3.select("#graph")
    graph.html("")

    //Save the data, and the current searchterm for future reference
    current_data = data
    current_term = searchterm

    //Remove all LeaderLine connections, that remained from last query result
    d3.selectAll(".leader-line").remove()

    //Lists storing various elements of the visualization, for future use
    headers = []
    lines = []
    column_list = []

    //For each key in the data, generate a new column with the information in it
    for (let key in data) { //Note: Not using "let" keyword here (and at other places in the code) results in incorrect callbacks

        let column_dict = data[key] //The metadata about each column
        let word_list_dict = column_dict.words //The word data of each column

        //Generate a column for each key
        var col = graph.append("div")
            .attr("class","col")
            .attr("data-similarity",column_dict["similarity_to_next"])
            .style("display","flex")
            .style("flex-direction","column")
        
        column_list.push(col)
        
        //Generate the headline of the column
        var header = col.append("H4")
            .attr("id","column_header")
            .text(key)

        headers.push(header)

        //Show the Document count for each column
        col.append("small")
            .attr("id","document_count")
            .text("Documents: " + column_dict.document_count.toString())


        //Sort the dictionary keys by their TFIDF value, to properly visually encode their relevance
        let keys = Object.keys(word_list_dict).sort(function(a, b) {
                return word_list_dict[a].tfidf - word_list_dict[b].tfidf
            }
        ).reverse()
        console.log(keys)
          
        //Generate the glyph for each word in a column
        for(let word of keys) { 
            //If the user explicitly deletes this word, remove it from the results
            if (deleted_nodes.includes(word)) continue
            //Get 2D embedding of word
            let formatted_color = position_to_color(word_list_dict[word].position)
            //Create a div which will contain each datapoint (circle+text)
            let cricle_div = col.append("div")

            var svg = cricle_div.append("svg")
                .attr("id","circle_div")
                .attr("width", 200)
                .attr("height", 150)
                .style("margin", "auto")
                .style("display", "block")
            //Get detail of current word to create starglyph
            let detail_data = word_list_dict[word].detail_data
            //Load data for starglyph from detail data

            //Create circle and starglyph
            circle = create_circle(svg,formatted_color,word,word_list_dict[word].tfidf) //#f3f3f3
                .on("click",function() {
                    current_column = key
                    current_date_from = column_dict.date_from
                    current_date_to = column_dict.date_to
                    current_detail = word
                    showModal(detail_data,formatted_color,word)
                })
            //initialize_starglyph(svg,word,column_dict.date_from,column_dict.date_to)
            create_starglyph(svg,detail_data,100,75,39,false) //Starglyph is 1 pixel smaller in radius to compensate for border
        }
    }

    //Create dashed lines between headers to visualize semantic change
    for(var i=1; i<headers.length; i++) {
        similarity = column_list[i-1].attr("data-similarity")
        var line = new LeaderLine(headers[i-1].node(), headers[i].node());
        line.setOptions({ 
            //size = 2,
            dash: {len: similarity*50+10, gap: 5},
            endPlug: "arrow1",
            color: 'rgb(0, 0, 0)',
            endPlugSize: 1,
            middleLabel: LeaderLine.pathLabel({
                text: parseFloat(1.0-similarity).toFixed(2),
                color: "grey",
                fontSize: "12.5px",
                outlineColor: ""
            })
        });
        line.size = 2
        lines.push(line)
    }

    //Create lines between circles of same text to visualize bridge terms
    for(var i=1; i<column_list.length; i++) {  
        let c_curr = column_list[i]
        let c_prev = column_list[i-1]

        c_curr.selectAll("#datacircle").each(function() {
            let e_curr = d3.select(this)

            c_prev.selectAll("#datacircle").each(function() {
                let e_prev = d3.select(this)
                if(e_curr.attr("data-text") === e_prev.attr("data-text")) {

                    var line = new LeaderLine(
                        e_prev.node(),
                        e_curr.node()
                    );

                    line.setOptions({ 
                        endPlug: "behind",
                        color: e_curr.style("stroke"),
                        startSocket: 'right',
                        endSocket: 'left'
                    });

                    line.size = 4
                    line.path = "fluid"
                    lines.push(line)
                }
            })
        })
    }

    //Move all leaderlines behind the glyphs, to avoid visual overlap
    d3.selectAll(".leader-line").style("z-index",-5)

    //Initialize tooltips (Redundant at the moment)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

}

//Creates a starglyph at given coordiante with given settings
// layout: The node under which to append the starglyph
// dict: The data the glyph shall represent
// cx, cy: the coordinate of the circle
// r: the radius of the circle
// showtext: wether the starglyph should be labeld with the terms at each corner
function create_starglyph(layout,dict,cx,cy,r,showtext = true) {
    var keys =  Object.keys(dict)
    var a_step = 2*Math.PI / keys.length // The angle between each element in the starglyph

    //Strings to later create the starglyph from
    pointstring = ""
    linepath = ""

    var centerpoint = "M" + cx.toString() + " " + cy.toString() + " "
    linepath += centerpoint + " "

    //Normalize the glyph so it takes up 100% of circle
    tfidf_list = []
    for(var i = 0; i<keys.length; i++) {
        var key = keys[i]
        tfidf_list.push(dict[key].tfidf)
    }

    //Localy scale the starglyph so the biggest value is 1
    var local_multiplier = 1.0 / Math.max(...tfidf_list)
    
    var gradient_points_list = []
    var color_list = []

    //For each key, generate another corner for the starglyph
    for(var i = 0; i<keys.length; i++) {
        var key = keys[i]
        var tfidf = dict[key].tfidf * local_multiplier
        var color = position_to_color(dict[key].position)
        color_list.push(color)

        var a = a_step * i 
        
        //Polygon points for the starglyph
        px = cx + (r*tfidf) * Math.cos(a)
        py = cy + (r*tfidf) * Math.sin(a)
        point = px.toString() + "," + py.toString()
        pointstring += point + " "

        //Polygon points for each 
        gradient_points_list.push([px,py])

        //Path for the light gray lines connecting center with circle radius
        px = cx + r * Math.cos(a)
        py = cy + r * Math.sin(a)
        point = "L" + px.toString() + " " + py.toString() + " "
        linepath += point + centerpoint

        //Add text at each endpoint of these path
        var textoffset = 15
        px = cx + (r+textoffset) * Math.cos(a)
        py = cy + (r+textoffset) * Math.sin(a)

        if (showtext) {

            textanchor = "middle"
            if(px > cx) textanchor = "start"
            else if (px < cx) textanchor = "end"

            let tfidf_text = layout.append("text")
                .attr("x",px)
                .attr("y",py + 20)
                .attr("text-anchor",textanchor)
                .attr("font-size",".8em")
                .style("opacity",0.0)
                .style("fill","grey")
                //HACK: This is hands down the ugliest workaround ive ever written and i hate myself
                .text("\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0 TF-IDF: " + parseFloat(dict[key].tfidf).toFixed(3) + "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0")

            let title_text = layout.append("text")
                .attr("x",px)
                .attr("y",py)
                .attr("dominant-baseline","middle")
                .attr("text-anchor",textanchor)
                .attr("font-size","1em")
                .text(key)
                .on("mouseover", function() {
                    tfidf_text.transition()
                        .duration("150")
                        .style("opacity",1.0)
                })
                .on("mouseout", function() {
                    tfidf_text.transition()
                        .duration("150")
                        .style("opacity",0.0)
                })

                //This code is supposed to move the TFIDF value text to the right spot under the term text, but it doesnt seem to work
                //Apparently getComputedTextLength is only available after one frame is rendered. TODO: fix this
                //length = title_text.node().getComputedTextLength()
                //console.log(length)
                //tfidf_text.attr("x",px - length)
        }
    }
    
    
    //Pathes needs to close off at the end
    linepath += "Z"
    color_list.push(color_list[0])
    gradient_points_list.push(gradient_points_list[0])

    var path = layout.append("path")
        .attr("id","starglyphpath")
        .attr("d",linepath)

    var glyph = layout.append("polygon")
        .attr("id","starglyph")
        .attr("points",pointstring)

    for(var i=1; i<gradient_points_list.length; i++) {
        px1 = gradient_points_list[i-1][0]
        py1 = gradient_points_list[i-1][1]
        px2 = gradient_points_list[i][0]
        py2 = gradient_points_list[i][1]

        //Generate a unique ID for the linear gradient to be referred by from the line HACK
        var uid = ("grad" + keys.join("") + i.toString()).split(' ').join('')
        var uid = uid.replace(/\W/g, '')

        //HACK: find out if its a small starglyph or the detailview one, and set line_width depending on it
        var line_width = 4
        if (r > 100.0) line_width = 7

        var linear_gradient = layout.append("linearGradient")
            .attr("id",uid)
            .attr("x1",px1)
            .attr("y1",py1)
            .attr("x2",px2)
            .attr("y2",py2)
            .attr("gradientUnits","userSpaceOnUse")
        linear_gradient.append("stop")
            .attr("offset","0%")
            .attr("stop-color",color_list[i-1])
        linear_gradient.append("stop")
            .attr("offset","100%")
            .attr("stop-color",color_list[i])

        layout.append("line")
            .attr("id","glyph-line")
            .attr("x1",px1)
            .attr("y1",py1)
            .attr("x2",px2)
            .attr("y2",py2)
            .style("stroke-width",line_width)
            .style("stroke","url(#" + uid +")")
            .style("pointer-events","none")
            .style("transform-origin", "50% 50%")
    }
}

// This function creates the glyph on the main view
// svg: the element to append the glyph to
// color: the color of the glyph
// text: The label of the glyph
// tfidf: the tfidf value of the glyph
function create_circle(svg,color,text,tfidf) {

    svg.append("text")
        .attr("x","50%")
        .attr("y","12%")
        .attr("text-anchor","middle")
        .attr("dy",".3em")
        .style("pointer-events", "none")
        .text(text)

    let tfidf_text = svg.append("text")
        .attr("id","tfidf-value")
        .attr("x","50%")
        .attr("y","93%")
        .attr("text-anchor","middle")
        .attr("font-size","0.8em")
        .style("pointer-events", "none")
        .style("fill","grey")
        .style("opacity","0.0")
        .text("TF-IDF: " + parseFloat(tfidf).toFixed(3)) //Cut the float back to 3 digits after comma
    
    circle = svg.append("circle")
        .attr("id","datacircle")
        .attr("class","section")
        .attr('cx', 100)
        .attr('cy', 75)
        .attr('r', 40)
        .attr('data-text',text)
        .style('stroke', color)
        .style("stroke-width", "4px")
        .style('fill', "#f3f3f3")
        .style('fill-opacity','50%')
        .style("transform-origin", "50% 50%")
        //Increase the glyphs size while hovering over it
        .on("mouseover", function() {
            tfidf_text.transition()
                .duration("150")
                .style("opacity",1.0)
            d3.select(this.parentNode).selectAll("#datacircle, #starglyph, #starglyphpath, #glyph-line").transition()
                .duration("250")
                .style("transform","scale(1.1)")
                
        })
        .on("mouseout", function() {
            tfidf_text.transition()
                .duration("150")
                .style("opacity",0.0)
            d3.select(this.parentNode).selectAll("#datacircle, #starglyph, #starglyphpath, #glyph-line").transition()
                .duration("250")
                .style("transform","scale(1.0)")
        })
        return circle
}

//TODO: This contains duplicate code
//Create the big glyph circle shown in the detail view
function create_glyph_circle(layout,data,color) {
    var cricle_div = layout.append("div")
    var cx = 300
    var cy = 200
    var r = 150
    var svg = cricle_div.append("svg")
        .attr("width", 600)
        .attr("height", 400)
        .style("margin", "auto")
        .style("display", "block")
    
    create_starglyph(svg,data,cx,cy,r-4)
    console.log(color)
    svg.append("circle")
        .attr("id","detail-glyph-circle")
        .attr('cx', cx)
        .attr('cy', cy)
        .attr('r', r)
        .style('stroke', color)
        .style("stroke-width","8px")
        .style('fill-opacity','0%')
}

//Opens the given url in the webbrowser
function openLink(url) {
    window.open(url, '_blank').focus();
}

//Opens up the detail view, and initalizes it
// detailData: the data the view is supposed to represent
// color: the color of the glyph in the detail view
// word: the term analyzed
function showModal(detailData,color,word) {
    var detailModal = new bootstrap.Modal(document.getElementById("detailModal"), {})

    //Remove the starglyph on close, preventing from linearGradients being overriden at the small circles
    var modalNode = document.getElementById('detailModal')
    modalNode.addEventListener('hidden.bs.modal', function (event) {
        d3.select("#starglpyh-div").selectAll("*").remove()
    })

    //Unbind all previous handlers, and add a new one for the current delete button
    $('#remove_button').off() 
    $('#remove_button').bind('click', function() {
        deleted_nodes.push(word)
        updateGraph(current_data)

        detailModal.hide()
    });
    //Unbind all previous handlers, and add a new one for the current apply button
    $('#apply_button').off() 
    $('#apply_button').bind('click', function() {
        current_data[current_column]["words"][word].detail_data = last_starglyph_query
        updateGraph(current_data)
        detailModal.hide()
    });

    //Set the title of the detail view
    $('#modal-title').html("Detail View for: " + "<b>" + word + "</b>")
    
    //Set the starting input to be the top 5 TFIDF terms, available in detailData
    starting_input = Object.keys(detailData).join(", ")
    $('#glyphterms').val(starting_input)
    detailModal.show()
    document.getElementById("starglyph-tab").click() //Emulate click on first tab element tor reset detail modal
    
    //Initializes the starglyph
    updateStarglyph(detailData,color)
}