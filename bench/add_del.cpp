// Copyright (c) 2015-2016 Vittorio Romeo
// License: Academic Free License ("AFL") v. 3.0
// AFL License page: http://opensource.org/licenses/AFL-3.0
// http://vittorioromeo.info | vittorio.romeo@outlook.com

#include "./utils/dependencies.hpp"

namespace example
{
    // Component definitions.
    namespace c
    {
        struct life
        {
            float _v;
            int _spawns;
        };
    }
}

// Component tags, in namespace `example::ct`.
EXAMPLE_COMPONENT_TAG(life);

// System tags, in namespace `example::st`.
EXAMPLE_SYSTEM_TAG(life);

// TODO:
namespace example
{
    template <typename TProxy>
    void mk_particle(TProxy& proxy, int spawns);
}

using ft = float;
namespace example
{
    namespace s
    {
        struct life
        {
            template <typename TData>
            void process(ft dt, TData& data)
            {
                data.for_entities([&](auto eid)
                    {
                        auto& l = data.get(ct::life, eid)._v;
                        auto& spawns = data.get(ct::life, eid)._spawns;
                        l -= 10.f * dt;

                        if(l <= 0.f)
                        {
                            data.kill_entity(eid);
                            if(spawns > 0)
                            {
                                data.defer([spawns](auto& proxy)
                                    {
                                        mk_particle(proxy, spawns - 1);
                                    });
                            }
                        }
                    });
            }
        };
    }

    // Compile-time `std::size_t` entity limit.
    constexpr auto entity_limit = ecst::sz_v<50000 * 2 * 2 * 2>;

    // Run-time initial particle count.
    sz_t initial_particle_count = 50000;

    namespace ecst_setup
    {
        // Builds and returns a "component signature list".
        constexpr auto make_csl()
        {
            namespace cs = ecst::signature::component;
            namespace csl = ecst::signature_list::component;

            constexpr auto cs_life = // .
                cs::make(ct::life).contiguous_buffer();

            return csl::make( // .
                cs_life       // .
                );
        }

        // Builds and returns a "system signature list".
        constexpr auto make_ssl()
        {
            // Signature namespace aliases.
            namespace ss = ecst::signature::system;
            namespace sls = ecst::signature_list::system;

            // Inner parallelism aliases and definitions.
            namespace ips = ecst::inner_parallelism::strategy;
            namespace ipc = ecst::inner_parallelism::composer;
            constexpr auto split_evenly_per_core =
                ips::split_evenly_fn::v_cores();

            constexpr auto ssig_life =                  // .
                ss::make(st::life)                      // .
                    .parallelism(split_evenly_per_core) // .
                    .write(ct::life);                   // .

            // Build and return the "system signature list".
            return sls::make( // .
                ssig_life     // .
                );
        }
    }

    template <typename TProxy>
    void mk_particle(TProxy& proxy, int spawns)
    {
        auto eid = proxy.create_entity();

        auto& ccl = proxy.add_component(ct::life, eid);
        ccl._v = rndf(2, 4);
        ccl._spawns = spawns;
    }

    template <typename TContext>
    void init_ctx(TContext& ctx)
    {
        ctx.step([&](auto& proxy)
            {
                for(sz_t i = 0; i < initial_particle_count; ++i)
                {
                    mk_particle(proxy, 300);
                }
            });
    }


    std::size_t remaining_waves = 2;

    template <typename TContext, typename TRenderTarget>
    void update_ctx(TContext& ctx, TRenderTarget& rt, ft dt)
    {
        namespace sea = ::ecst::system_execution_adapter;



        ctx.step([&rt, dt](auto& proxy)
            {
                proxy.execute_systems()(
                    sea::t(st::life).for_subtasks([dt](auto& s, auto& data)
                        {
                            s.process(dt, data);
                        }));
            });


        ctx.step([&](auto& proxy)
            {
                if(!proxy.any_entity_in(st::life))
                {
                    // std::cout << "rng test:" << rndf(0, 100) << "\n";
                    std::cout << initial_particle_count << ": ";
                    example::bench();

                    if(remaining_waves > 0)
                    {
                        --remaining_waves;
                        initial_particle_count *= 2;
                        example::reseed();
                        init_ctx(ctx);
                    }
                    else
                    {
                        example::_running = false;
                    }
                }
            });
    }
}

#include "./utils/pres_game_app.hpp"

namespace impl
{
    template <typename TEntityCount, typename TCSL, typename TSSL>
    auto make_settings_list(TEntityCount ec, TCSL csl, TSSL ssl)
    {
        namespace cs = ecst::settings;
        namespace ss = ecst::scheduler;
        namespace mp = ecst::mp;
        namespace bh = ecst::bh;

        (void)csl;
        (void)ssl;

        // List of threading policies.
        constexpr auto l_threading = mp::list::make( // .
            ecst::settings::impl::v_allow_inner_parallelism,
            ecst::settings::impl::v_disallow_inner_parallelism);

        // List of storage policies.
        constexpr auto l_storage = mp::list::make( // .
            ecst::settings::fixed<decltype(ec){}>,
            ecst::settings::dynamic<50000>);

        (void)l_threading;
        (void)l_storage;

        return bh::fold_right(l_threading, mp::list::empty_v,
            [=](auto x_threading, auto xacc)
            {
                auto fold2 = bh::fold_right(l_storage, mp::list::empty_v,
                    [=](auto y_storage, auto yacc)
                    {
                        auto zsettings =                    // .
                            cs::make()                      // .
                                .set_threading(x_threading) // .
                                .set_storage(y_storage)     // .
                                .component_signatures(csl)  // .
                                .system_signatures(ssl)     // .
                                .scheduler(cs::scheduler<ss::s_atomic_counter>);


                        return bh::append(yacc, zsettings);
                    });

                return bh::concat(xacc, fold2);
            });
    }

    template <typename TSettings>
    auto make_ecst_context(TSettings)
    {
        return ecst::context::make(TSettings{});
    }

    template <typename TSettings, typename TF>
    void do_test(TSettings, TF&& f)
    {
        // Create context.
        using context_type = decltype(make_ecst_context(TSettings{}));
        auto ctx_uptr = std::make_unique<context_type>();
        auto& ctx = *ctx_uptr;

        f(ctx);
    }
}

template <typename TF, typename TEntityCount, typename TCSL, typename TSSL>
void run_tests(TF&& f, TEntityCount ec, TCSL csl, TSSL ssl)
{
    using vrm::core::sz_t;
    constexpr sz_t times = 3;

    using hr = std::chrono::high_resolution_clock;
    using d_type = std::chrono::duration<float, std::milli>;


    for(sz_t t = 0; t < times; ++t)
    {
        std::cout << "run " << t << "\n";
        ecst::bh::for_each(impl::make_settings_list(ec, csl, ssl), [f](auto s)
            {
                std::cout << ecst::settings::str::entity_storage<decltype(s)>()
                          << "\n"
                          << ecst::settings::str::multithreading<decltype(s)>()
                          << "\n";

                impl::do_test(s, f);
            });
    }

    std::cout << "\n\n\n";
}

int main()
{
    auto doit = [&](auto& ctx)
    {
        // Run the simulation.
        example::initial_particle_count = 50000;
        example::_running = true;
        example::remaining_waves = 2;
        example::reseed();
        example::run_simulation(ctx);
    };

    run_tests(doit, example::entity_limit, example::ecst_setup::make_csl(),
        example::ecst_setup::make_ssl());
}