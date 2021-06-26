var current_term = "climate change"
var current_detail = "climate change"
var current_date_from = "2001-01"
var current_date_to = "2001-10"
var current_column
var last_starglyph_query
var current_data = {}

var lines = []
var deleted_nodes = []

window.requestAnimationFrame(redraw_lines);


$(function() {
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
});


function redraw_lines() {
    for(l of lines) {
        l.position()
    }
    window.requestAnimationFrame(redraw_lines);
    //console.log("SCOLL")
}

//Function that is called when the starglyph tab is opened in the detail tab
function updateStarglyph(data,color) {
    console.log(data)
    last_starglyph_query = data
    var tab = d3.select("#starglpyh-div")
    tab.selectAll("*").remove()
    create_glyph_circle(tab,data,color)
}

function updateConcordance(data) {
    var table_body = d3.select("#concordance_table")

    var count = 0
    max_count = 50
    for(let occurance of data) {
        count += 1
        if(count > max_count) break

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

function updateGraph(data) {
    console.log(data)
    current_data = data
    interval = d3.select("#graph")
    searchterm = d3.select("#searchterm").property("value")
    
    var graph = d3.select("#graph")
    graph.html("")

    current_term = searchterm

    d3.selectAll(".leader-line").remove()

    headers = []
    lines = []
    column_list = []

    //For each key in the data, generate a new column with the information in it
    for (let key in data) {

        let column_dict = data[key]
        let word_list_dict = column_dict.words

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


        let keys = Object.keys(word_list_dict).sort(function(a, b) {
                return word_list_dict[a].tfidf - word_list_dict[b].tfidf
            }
        ).reverse()
        console.log(keys)
          
        //console.log(word_dict)
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
    
    d3.selectAll(".leader-line")
        .attr("data-bs-toggle", "tooltip")
        .attr("data-bs-placement","top")
        .attr("title","Tooltip on top")

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

    d3.selectAll(".leader-line").style("z-index",-5)
    //var uff = d3.selectAll(".leader-line").remove().each(function() {
    //    d3.select("#graph").append(this)
    //})
    
    //document.getElementById('graph').appendChild(document.querySelector('.leader-line'));
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

}

function create_starglyph(layout,dict,cx,cy,r,showtext = true) {
    pointstring = ""
    linepath = ""

    var keys =  Object.keys(dict)
    var a_step = 2*Math.PI / keys.length // The angle between each element in the starglyph

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

        textanchor = "middle"
        if(px > cx) textanchor = "start"
        else if (px < cx) textanchor = "end"

        if (showtext) {
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

                //length = title_text.node().getComputedTextLength()
                //console.log(length)
                //tfidf_text.attr("x",px - length)
        }
    }
    
    
    //Linepath needs to close off at the end
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

        //Generate a unique ID for the linear gradient to be referred by from the line
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
        .text("TF-IDF: " + parseFloat(tfidf).toFixed(3))
    
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

function openLink(url) {
    window.open(url, '_blank').focus();
}

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

    $('#modal-title').html("Detail View for: " + "<b>" + word + "</b>")
    
    starting_input = Object.keys(detailData).join(", ")
    $('#glyphterms').val(starting_input)
    detailModal.show()
    document.getElementById("starglyph-tab").click() //Emulate click on first tab element tor reset detail modal
    updateStarglyph(detailData,color)
}