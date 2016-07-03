// Copyright (c) 2015-2016 Vittorio Romeo
// License: Academic Free License ("AFL") v. 3.0
// AFL License page: http://opensource.org/licenses/AFL-3.0
// http://vittorioromeo.info | vittorio.romeo@outlook.com

#pragma once

#include "./dependencies.hpp"

namespace example
{
    template <typename TProxy>
    void mk_particle(TProxy& proxy, const vec2f& position, float radius);

    template <typename TContext>
    class game_app : public boilerplate::app
    {
    private:
        using this_type = game_app;
        TContext& _ctx;

        float _delay{0.f};
        bool _draw_grid{false}, _kill_pls{false};

        void init_loops()
        {
            std::chrono::high_resolution_clock hrc;
            using ft_dur = std::chrono::duration<ft, std::ratio<1, 1000>>;

            ft dt = 0.04f;

            while(true)
            {
                auto cb = hrc.now();


                sf::Event e;
                while(window().pollEvent(e))
                {
                }

                window().clear();

                auto mposi = sf::Mouse::getPosition(window());
                auto ws = window().getSize();

                if(mposi.x < (int)0) mposi.x = 0;
                if(mposi.x > (int)ws.x) mposi.x = ws.x;

                if(mposi.y < (int)0) mposi.y = 0;
                if(mposi.y > (int)ws.y) mposi.y = ws.y;

                vec2f mpos = window().mapPixelToCoords(mposi);

                update_ctx(_ctx, this->window(), dt);

                window().display();
                auto ce = hrc.now();
                auto real_dt =
                    std::chrono::duration_cast<ft_dur>(ce - cb).count();

                // TODO:
                auto fps = 1.f / real_dt * 1000.f;

                window().setTitle(std::string{"DT: "} +
                                  std::to_string(real_dt) + "  |  FPS: " +
                                  std::to_string(fps));



                if(!_running)
                {
                    break;
                }
            }
        }


        void init()
        {

            init_ctx(_ctx);
            init_loops();
        }

    public:
        game_app(sf::RenderWindow& window, TContext& ctx) noexcept
            : boilerplate::app{window},
              _ctx{ctx}
        {
            init();
        }
    };

    template <typename TContext>
    void run_simulation(TContext& ctx)
    {
        boilerplate::app_runner<game_app<ECST_DECAY_DECLTYPE(ctx)>> x{
            "Particle ECST test", 1440, 900, ctx};

        x.run();
    }
}
