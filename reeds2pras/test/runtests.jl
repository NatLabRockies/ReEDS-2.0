using ReEDS2PRAS
using BenchmarkTools
using Aqua
using DataFrames
using PRAS
using Test

const R2P = ReEDS2PRAS
include("utils.jl")

@testset verbose = true "Aqua.jl" begin
    Aqua.test_unbound_args(ReEDS2PRAS)
    Aqua.test_undefined_exports(ReEDS2PRAS)
    Aqua.test_ambiguities(ReEDS2PRAS)
    Aqua.test_stale_deps(ReEDS2PRAS)
    Aqua.test_deps_compat(ReEDS2PRAS)
end

#=
Don't add your tests to runtests.jl. Instead, create files named

    test-title-for-my-test.jl

The file will be automatically included inside a `@testset` with title "Title For My Test".
=#
@testset verbose = true "ReEDS2PRAS tests" begin
    for (root, dirs, files) in walkdir(@__DIR__)
        for file in files
            if isnothing(match(r"^test.*\.jl$", file))
                continue
            end
            title = titlecase(replace(splitext(file[6:end])[1], "-" => " "))
            @testset verbose = true  "$title" begin
                include(file)
            end
        end
    end
end