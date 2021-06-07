var current_term = "climate change"
var current_detail = "climate change"
var current_date_from = "2001-01"
var current_date_to = "2001-10"

var lines = []

window.requestAnimationFrame(redraw_lines);

$(function() {
    Color2D.setColormap(Color2D.colormaps.ZIEGLER, function() {}); 
    $('#submit').bind('click', function() {
        $.getJSON('/_search_term', {
        term: $('#searchterm').val(),
        interval: $('#interval_dropdown').val(),
        from: $('#datefrom').val(),
        to: $('#dateto').val(),
        count: $('#resultcount').val(),
        deep: true
        }, function(data) {
            updateGraph(data.result)
        });
        return false;
    });
    
    $('#starglyph-tab').bind('click', function() {
        var tab_body = d3.select("#content_starglyph")
        tab_body.selectAll("*").remove()

        $.getJSON('/_search_term', {
        term: current_detail,
        interval: $('#interval_dropdown').val(),
        from: current_date_from,
        to: current_date_to,
        count: 5,
        deep: false,
        }, function(data) {
            updateStarglyph(data.result)
        });
        return false;
    });
    
    $('#concordance-tab').bind('click', function() {
        var table_body = d3.select("#concordance_table")
        table_body.selectAll("*").remove()

        $.getJSON('/_get_concordance', {
        term: current_term,
        word: current_detail,
        from: current_date_from,
        to: current_date_to,
        }, function(data) {
            updateConcordance(data.result)
        });
        return false;
    });
});


function redraw_lines() {
    return
    for(l of lines) {
        l.position()
    }
    window.requestAnimationFrame(redraw_lines);
    //console.log("SCOLL")
}

//Function that is called when the starglyph tab is opened in the detail tab
function updateStarglyph(data) {
    console.log(data)
    var tab = d3.select("#content_starglyph")
    
    for (let key in data) {
        let column_dict = data[key]
        let word_list_dict = column_dict.words
        //console.log(word_dict)

        glyphdata = {}
        for(let word of Object.keys(word_list_dict)) { 
            //Random data for starglyph
            glyphdata[word] = word_list_dict[word].tfidf
        }
        //Create starglyph
        create_glyph_circle(tab,word_list_dict)
        break //There should not be more than one column anyway
    }
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

function initialize_starglyph(svg,term,from,to) {
    $.getJSON('/_search_term', {
        term: term,
        interval: $('#interval_dropdown').val(),
        from: from,
        to: to,
        count: 5,
    }, function(data) {
        updateGraph(data.result)

        for (let key in data) {
            let column_dict = data[key]
            let word_list_dict = column_dict.words
            //console.log(word_dict)
    
            glyphdata = {}
            for(let word of Object.keys(word_list_dict)) { 
                //Random data for starglyph
                glyphdata[word] = word_list_dict[word].tfidf
            }
            //Create starglyph
            create_starglyph(svg,glyphdata,100,75,39,false)
            break //There should not be more than one column anyway
        }
    });
    return false;  
}

function updateGraph(data) {
    console.log(data)
    interval = d3.select("#graph")
    searchterm = d3.select("#searchterm").property("value")
    
    var graph = d3.select("#graph")
    graph.html("")

    current_term = searchterm

    d3.selectAll(".leader-line").remove()

    headers = []
    lines = []
    column_list = []
    
    for (let key in data) {
        var col = graph.append("div")
            .attr("class","col")
            .style("display","flex")
            .style("flex-direction","column")
        
        column_list.push(col)
        
        var header = col.append("H4")
            .attr("id","column_header")
            .text(key)
            .attr("data-bs-toggle", "tooltip")
            .attr("data-bs-placement","top")
            .attr("title","Tooltip on top")

        headers.push(header)

        let column_dict = data[key]
        let word_list_dict = column_dict.words
        //console.log(word_dict)
        for(let word of Object.keys(word_list_dict)) { 
            //Get 2D embedding of word
            var formatted_color = position_to_color(word_list_dict[word].position)
            //Create a div which will contain each datapoint (circle+text)
            var cricle_div = col.append("div")
            var svg = cricle_div.append("svg")
                .attr("id","circle_div")
                .attr("width", 200)
                .attr("height", 150)
                .style("margin", "auto")
                .style("display", "block")

            //Get detail of current word to create starglyph
            var detail_data = word_list_dict[word].detail_data
            //Load data for starglyph from detail data

            //Create circle and starglyph
            circle = create_circle(svg,formatted_color,word) //#f3f3f3
            .on("click",function() {
                current_date_from = column_dict.date_from
                current_date_to = column_dict.date_to
                current_detail = word
                showModal()
            })
            //initialize_starglyph(svg,word,column_dict.date_from,column_dict.date_to)
            create_starglyph(svg,detail_data,100,75,39,false) //Starglyph is 1 pixel smaller in radius to compensate for border
        }
    }

    //Create dashed lines between headers to visualize semantic change
    for(var i=1; i<headers.length; i++) {
        var line = new LeaderLine(headers[i-1].node(), headers[i].node());
        line.setOptions({ 
            //size = 2,
            dash: {len: Math.random()*50+10, gap: 5},
            endPlug: "arrow1",
            color: 'rgb(0, 0, 0)',
            endPlugSize: 1,
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
        var c_curr = column_list[i]
        var c_prev = column_list[i-1]

        c_curr.selectAll("circle").each(function() {
            e_curr = d3.select(this)

            c_prev.selectAll("circle").each(function() {
                e_prev = d3.select(this)
                if(e_curr.attr("data-text") === e_prev.attr("data-text")) {

                    var line = new LeaderLine(
                        e_prev.node(),
                        e_curr.node()
                    );

                    line.setOptions({ 
                        endPlug: "behind",
                        color: 'rgb(0, 0, 0)',
                        startSocket: 'right',
                        endSocket: 'left'
                    });
                    line.size = 2
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
    gradientpath = ""

    var keys =  Object.keys(dict)
    var a_step = 2*Math.PI / keys.length // The angle between each element in the starglyph

    var centerpoint = "M" + cx.toString() + " " + cy.toString() + " "
    linepath += centerpoint + " "
    
    var color_list = []
    for(var i = 0; i<keys.length; i++) {
        var key = keys[i]
        var tfidf = dict[key].tfidf
        var color = position_to_color(dict[key].position)
        color_list.push(color)

        var a = a_step * i 
        
        //Polygon points for the starglyph
        px = cx + (r*tfidf) * Math.cos(a)
        py = cy + (r*tfidf) * Math.sin(a)
        point = px.toString() + "," + py.toString()
        pointstring += point + " "
        if(i==0)
            gradientpath += "M" + px.toString() + " " + py.toString() + " "
        else 
            gradientpath += "L" + px.toString() + " " + py.toString() + " "

        //Path for the light gray lines connecting center with circle radius
        px = cx + r * Math.cos(a)
        py = cy + r * Math.sin(a)
        point = "L" + px.toString() + " " + py.toString() + " "
        linepath += point + centerpoint

        //Add text at each endpoint of these path
        var textoffset = 10
        px = cx + (r+textoffset) * Math.cos(a)
        py = cy + (r+textoffset) * Math.sin(a)

        textanchor = "middle"
        if(px > cx) textanchor = "start"
        else if (px < cx) textanchor = "end"

        if (showtext) {
            layout.append("text")
                .attr("x",px)
                .attr("y",py)
                .attr("text-anchor",textanchor)
                .attr("stroke","51c5cf")
                .attr("stroke-width","20px")
                .attr("dy",".3em")
                .text(key)
        }

    }
    color_list.push(color_list[0])
    //Linepath needs to close off at the end
    linepath += "Z"
    gradientpath += "Z"


    var path = layout.append("path")
        .attr("id","starglyphpath")
        .attr("d",linepath)
    var glyph = layout.append("polygon")
        .attr("id","starglyph")
        .attr("points",pointstring)

    var gradient_path = layout.append("path")
        .attr("id","starglyphgradient")
        .attr("d",gradientpath)
    generatePathGradient(d3.select(layout.node()),"#starglyphgradient",color_list)



        
}


function create_circle(svg,color,text) {
    circle = svg.append("circle")
        .attr("id","datacircle")
        .attr("class","section")
        .attr('cx', 100)
        .attr('cy', 75)
        .attr('r', 40)
        .attr('stroke', color)
        .attr("stroke-width","3px")
        .attr('fill', "#f3f3f3")
        .attr('fill-opacity','50%')
        .attr('data-text',text)
        //.attr("data-bs-toggle","modal")
        //.attr("data-bs-target","#detailModal")

    svg.append("text")
        .attr("x","50%")
        .attr("y","15%")
        .attr("text-anchor","middle")
        .attr("stroke","51c5cf")
        .attr("stroke-width","20px")
        .attr("dy",".3em")
        .style("pointer-events", "none")
        .text(text.split(" ").join("\n"))
    
        return circle
}

function create_glyph_circle(layout,data) {
    var cricle_div = layout.append("div")
    var cx = 300
    var cy = 200
    var r = 150
    var svg = cricle_div.append("svg")
        .attr("width", 600)
        .attr("height", 400)
        .style("margin", "auto")
        .style("display", "block")
    
    create_starglyph(svg,data,cx,cy,r)

    svg.append("circle")
        .attr('cx', cx)
        .attr('cy', cy)
        .attr('r', r)
        .attr('stroke', 'black')
        .attr("stroke-width","4px")
        //.attr('fill', color)
        .attr('fill-opacity','0%')
        .on("click")
}

function openLink(url) {
    window.open(url, '_blank').focus();
}

function showModal() {
    var myModal = new bootstrap.Modal(document.getElementById("detailModal"), {})
    
    myModal.show()
    document.getElementById("starglyph-tab").click() //Emulate click on first tab element tor reset detail modal
}

