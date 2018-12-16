local function starts_with(str, start)
   return str:sub(1, #start) == start
end

local function wrap_displayed_equation(text)
    return '<div class="displayed-math">' .. text .. '</div>'
end

local function wrap_reference(text)
    return '<span class="equation-reference">' .. text .. '</span>'
end


function RawInline(elem)
    if starts_with(elem.text, '\\ref') then
        return pandoc.RawInline('html', wrap_reference(elem.text))
    else
        return pandoc.RawInline('html', wrap_displayed_equation(elem.text))
    end
end


function Math(elem)
    return pandoc.RawInline('html',
        '<span class="inline-math">' .. elem.text .. '</span>')
end
