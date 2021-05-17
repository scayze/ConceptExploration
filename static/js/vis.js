

$(function() {
    Color2D.setColormap(Color2D.colormaps.ZIEGLER, function() {}); 
    $('#submit').bind('click', function() {
        $.getJSON('/_search_term', {
        term: $('#searchterm').val(),
        interval: $('#interval_dropdown').val(),
        from: $('#datefrom').val(),
        to: $('#dateto').val(),
        count: $('#resultcount').val(),
        }, function(data) {
            updateGraph(data.result)
        });
        return false;
    });
});

$(function() {
    $('#testbutton').bind('click', function() {
        console.log(document.getElementById("detailModal"))
    });
});

function updateGraph(data) {
    interval = d3.select("#graph")
    searchterm = d3.select("#searchterm").text()
    var graph = d3.select("#graph")
    graph.html("")

    d3.selectAll(".leader-line").remove()

    headers = []
    column_list = []
    
    for (var key in data) {
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

        word_dict = data[key]
        //console.log(word_dict)
        for(var word of Object.keys(word_dict)) { 
            //Get 2D embedding of word
            var data_2d = word_dict[word]

            //Clamp values to bettter fit data in colormap, creating more varied colors
            var xrange = [-2,4.5]
            var yrange = [-2,2.5]
            data_2d[0] = Math.max( xrange[0], Math.min(data_2d[0], xrange[1]))
            data_2d[1] = Math.max( yrange[0], Math.min(data_2d[1], yrange[1]))
            Color2D.ranges = {x: xrange, y: yrange}; 
            var rgb = Color2D.getColor(data_2d[0], data_2d[1])
            //Convert color to css color value
            var formatted_color = "rgb(" + rgb[0].toString() + ", " + rgb[1].toString() + ", " + rgb[2].toString() + ")" 
            console.log(word + " " + data_2d.toString() + " " + rgb.toString())

            //Create a div which will contain each datapoint (circle+text)
            var cricle_div = col.append("div")
            var svg = cricle_div.append("svg")
                .attr("id","circle_div")
                .attr("width", 150)
                .attr("height", 150)
                .style("margin", "auto")
                .style("display", "block")

            //Random data for starglyph
            glyphdata = {"a": Math.random(), "b": Math.random(), "c": Math.random(), "d": Math.random(), "e": Math.random()}
            //Create circle and starglyph
            circle = create_circle(svg,formatted_color,word) //#f3f3f3
            create_starglyph(svg,glyphdata,75,75,39,false) //Starglyph is 1 pixel smaller in radius to compensate for border
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
    }
    
    d3.selectAll(".leader-line")
        .attr("data-bs-toggle", "tooltip")
        .attr("data-bs-placement","top")
        .attr("title","Tooltip on top")

    //Create lines between circles of same text to visualize bridge terms
    console.log(column_list.length)
    for(var i=1; i<column_list.length; i++) {  
        var c_curr = column_list[i]
        var c_prev = column_list[i-1]

        c_curr.selectAll("circle").each(function() {
            e_curr = d3.select(this)

            c_prev.selectAll("circle").each(function() {
                e_prev = d3.select(this)
                if(e_curr.attr("data-text") === e_prev.attr("data-text")) {
                    /* This alternative is for lines starting at the center of circles
                    var line = new LeaderLine(
                        LeaderLine.pointAnchor(e_prev.node(), {x: 41, y: 41}),
                        LeaderLine.pointAnchor(e_curr.node(), {x: 41, y: 41})
                    );
                    */
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
                }
            })
        })
    }

    d3.selectAll(".leader-line").style("z-index",-5)
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
    
    for(var i = 0; i<keys.length; i++) {
        var key = keys[i]
        var val = dict[key]

        var a = a_step * i 
        
        //Polygon points for the starglyph
        px = cx + (r*val) * Math.cos(a)
        py = cy + (r*val) * Math.sin(a)
        point = px.toString() + "," + py.toString()
        pointstring += point + " "

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
                .text("label")
        }

    }
    //Linepath needs to close off at the end
    linepath += "Z"


    var path = layout.append("path")
        .attr("id","starglyphpath")
        .attr("d",linepath)


    var glyph = layout.append("polygon")
        .attr("id","starglyph")
        .attr("points",pointstring)
        
}


function create_circle(svg,color,text) {
    circle = svg.append("circle")
        .attr("id","datacircle")
        .attr("class","section")
        .attr('cx', 75)
        .attr('cy', 75)
        .attr('r', 40)
        .attr('stroke', color)
        .attr("stroke-width","3px")
        .attr('fill', "#f3f3f3")
        .attr('fill-opacity','50%')
        .attr('data-text',text)
        //.attr("data-bs-toggle","modal")
        //.attr("data-bs-target","#detailModal")
        .on("click",showModal)

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

function create_glyph_circle(layout,color,text) {
    var cricle_div = layout.append("div")
    var cx = 200
    var cy = 200
    var r = 150
    var svg = cricle_div.append("svg")
        .attr("width", 400)
        .attr("height", 400)
        .style("margin", "auto")
        .style("display", "block")
    
    create_starglyph(svg,{"hallo": 0.5, "hello": 0.6, "hoi": 1.0, "bonjour": 0.8, "Moin": 1.0},cx,cy,r)

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


function showModal() {
    console.log("HALLO")
    var myModal = new bootstrap.Modal(document.getElementById("detailModal"), {})

    var view = d3.select("#content_starglyph")
    view.selectAll("*").remove();
    create_glyph_circle(view,"green","aaaa")
    var view = d3.select("#content_concordance")
    //view.selectAll("*").remove();
    //view.append("div").text("CONC")

    
    //create_starglyph(svg,{"hallo": 0.5, "hello": 0.6, "hoi": 1.0, "bonjour": 0.8, "Moin": 1.0})
    myModal.show()
}

