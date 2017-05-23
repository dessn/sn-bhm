r""" My attempt at a proper STAN model.


Parameters
----------

**Cosmological parameters**:

    * :math:`\Omega_m`: matter density
    * :math:`w`: dark energy equation of state
    * :math:`\alpha`: Phillips correction for stretch
    * :math:`\beta`: Tripp correction for colour

**Population parameters**:

    * :math:`\langle M_B \rangle`: mean absolute magnitude of supernova
    * :math:`\sigma_{M_B}`: standard deviation of absolute magnitudes
    * :math:`\langle c_i \rangle`: mean colour, as a function of redshift
    * :math:`\sigma_c`: standard deviation of  colour
    * :math:`\langle x_{i1} \rangle`: mean scale, as a function of redshift
    * :math:`\sigma_{x_1}`: standard deviation of scale
    * :math:`\rho`: correlation (matrix) between absolute magnitude, colour and stretch

**Marginalised parameters**:

    * :math:`\delta(0)` and :math:`\delta(\infty)`: The magnitude-mass relationship
    * :math:`\delta \mathcal{Z}_b`: Zeropoint uncertainty for each of the *g,r,i,z* bands.

**Per supernova parameters**:

    * :math:`m_B`: the true (latent) apparent magnitude
    * :math:`x_1`: the true (latent) stretch
    * :math:`c`: the true (latent) colour
    * :math:`z`: the true redshift of the supernova
    * :math:`m`: the true mass of the host galaxy

----------

Model Overview
--------------

We wish to model our posterior, given our observations, our model :math:`\theta`, and
selection effects :math:`S`.
Our specific observations :math:`D` are the light curves themselves,
the summary statistics that result from them :math:`\lbrace \hat{m_B}, \hat{c}, \hat{x_1} \rbrace`,
the covariance for the summary statistics :math:`\hat{C}`, the redshifts of the
object :math:`\hat{z}` and a normalised mass estimate :math:`\hat{m}`. We thus signify
observed variables with the hat operator. In this work we will be modelling
:math:`\lbrace \hat{m_B}, \hat{c}, \hat{x_1} \rbrace` as having true underlying
values, however assume that  :math:`\hat{z}` and :math:`\hat{m}` are
known :math:`(\hat{z} = z,\ \hat{m}=m)`.

For simplicity, we adopt the commonly used notation that :math:`\eta\equiv \lbrace \hat{m_B}, \hat{c}, \hat{x_1} \rbrace`.


.. math::
    :label: a

    P(\theta|D) &\propto \mathcal{L}(D|\theta, S) P(\theta) \\

with

.. math::
    :label: b

    \mathcal{L}(D|\theta, S) &= \frac{P(S | D, \theta) P(D|\theta)}{\int P(S|R, \theta) P(R|\theta) \ dR}, \\

where :math:`R` represents all possible data. To simplify notation in the future
I define :math:`w \equiv \int P(S|R, \theta) P(R|\theta) \ dR`.


----------

STAN Model
----------

Let us examine only the numerator for the time being. The numerator is the model
which ends up implemented in STAN, whilst the denominator can be implemented
differently. For simplicity, let us denote the population parameters
:math:`\lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle, \sigma_{M_B}, \sigma_{x_1}, \sigma_c, \rho \rbrace`
shown under the Population header as :math:`\gamma`.

Furthermore, in the interests of simplicity, let us examine only a single supernova for the time being. 
Let us denote the unnormalised likelihood for a single
supernova as :math:`P (D_i|\theta)`.

.. math::
    :label: d

    P (D_i|\theta) P(\theta) &= P(\hat{m_B}, \hat{x_1}, \hat{c}, \hat{z}, \hat{m} |
    \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m)
    P(\Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m) \\

Now, let us quickly deal with the priors so I don't have to type them out again and again.
We will treat :math:`\sigma_{M_B},\ \sigma_{x_1},\, \sigma_c`
with Cauchy priors, :math:`\rho` with an LKJ prior, :math:`\delta \mathcal{Z}_b` is constrained by
zero point uncertainty from photometry (currently just set to 0.01 mag normal uncertainty)
and other parameters with flat priors. The prior
distributions on redshift and host mass do not matter in this likelihood (without bias corrections),
as we assume redshift and mass are precisely known.
So now we can focus on the likelihood, and introduce latent variables :math:`\eta` to represent the true values
from which the observations are drawn from.

.. math::
    :label: e

    P (D_i|\theta) &= \iiint d\eta \  P(\hat{\eta}, \eta |  z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b )  \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]

.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::

        P (D_i|\theta) &= P(\hat{m_B}, \hat{x_1}, \hat{c}, \hat{z}, \hat{m} |
        \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m) \\[10pt]
        &= \int dm_B \int dx_1 \int dc \  P(\hat{m_B}, \hat{x_1}, \hat{c}, \hat{z}, \hat{m}, m_B, x_1, c | \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m) \\[10pt]
        &= \iiint d\eta \  P(\hat{\eta}, \hat{z}, \hat{m}, \eta | \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m) \\[10pt]
        &= \iiint d\eta \  \delta(\hat{z} - z) \delta(\hat{m}-m) P(\hat{\eta}, z, m, \eta | \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b, z, m) \\[10pt]
        &= \iiint d\eta \  P(\hat{\eta}, \eta |  z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b )  \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]

Where I have used the fact that we assume mass and redshift are precisely known
(:math:`\hat{z}=z` and :math:`\hat{m}=m`), and therefore do not need to be modelled with latent parameters. With precise
measurements, we do not need to consider the underlying redshift and mass distributions
:math:`P(z|\theta)` and :math:`P(m|\theta)` in this part of our model, as they will simply
modify the constant of proportionality, and thus I do not write them out.

We take zeropoint uncertainty into account by computing :math:`\frac{\partial\hat{\eta}}{\partial\mathcal{Z}_b}` for each supernova
light curve. We thus model what would be the observed values :math:`\hat{\eta}_{\rm True} = \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}_b}`,
and then assume that true observed summary statistics :math:`\hat{\eta}_{\rm True}` are normally
distributed around the true values :math:`\eta`, we can separate them out.

.. math::
    :label: eg

    P (D_i|\theta) &= \iiint d\eta \  \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}_b} |\eta, C \right) P(\eta| z, m, \Omega_m, w, \alpha, \beta, \gamma)  \delta(\hat{z} - z) \delta(\hat{m}-m)  \\


.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::

        P (D_i|\theta) &= \iiint d\eta \  P(\hat{\eta} | \eta, z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b ) P(\eta| z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta \mathcal{Z}_b ) \delta(\hat{z} - z) \delta(\hat{m}-m)  \\[10pt]
        &= \iiint d\eta \  P(\hat{\eta} | \eta, \delta \mathcal{Z}_b) P(\eta | z, m, \Omega_m, w, \alpha, \beta, \gamma)  \delta(\hat{z} - z) \delta(\hat{m}-m)  \\[10pt]
        &= \iiint d\eta \  \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}_b} |\eta, C \right) P(\eta| z, m, \Omega_m, w, \alpha, \beta, \gamma)  \delta(\hat{z} - z) \delta(\hat{m}-m)  \\

Now, in order to calculate :math:`P(\eta| \Omega_m, w, \alpha, \beta, \gamma, z, m, \delta\mathcal{Z}_b)`,
we need to transform from :math:`m_B` to :math:`M_B`. We transform using the following relationship:

.. math::
    :label: f

    M_B = m_B - \mu + \alpha x_1 - \beta c + k(z) m

where we define :math:`\mu` as


.. math::
    :label: g

    \mu &= 5 \log_{10} \left[ \frac{(1 + z)c}{H_0 \times 10{\rm pc}} \int_0^z \left(
    \Omega_m (1 + z)^3 + (1 - \Omega_m)(1+z)^{3(1+w)} \right) \right] \\

and :math:`k(z)` as

.. math::
    :label: h

    k(z) &= \delta(0) \left[ \frac{1.9\left( 1 - \frac{\delta(\infty)}{\delta(0)}
    \right)}{0.9 + 10^{0.95z}} + \frac{\delta(\infty)}{\delta(0)} \right] \\

We note that :math:`\mu` is a function of :math:`\hat{z},\Omega_m,w`, however we will simply denote it
:math:`\mu` to keep the notation from spreading over too many lines.

From the above,  :math:`M_B` is a function of :math:`\Omega_m, w, \alpha, \beta, x_1, c, z, m`. Or, more probabilistically,

.. math::
    P(M_B, m_B) = \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right).

We can thus introduce a latent variable :math:`M_B` and immediately remove the :math:`m_B` integral via the delta function.

.. math::
    :label: i

    P (D_i|\theta) &= \iiint d\eta  \int dM_B \  \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}_b} | \eta, C \right) P(\eta, M_B | z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta\mathcal{Z}_b) \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]

where

.. math::
    :label: igg

    P(\eta, M_B| \theta) &= \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]

.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::
        :label: ig

        P(\eta, M_B| \theta) &= P(m_B | M_B, x_1, c, z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta\mathcal{Z}_b ) P (M_B, x_1, c, | z, m, \Omega_m, w, \alpha, \beta, \gamma, \delta\mathcal{Z}_b )\delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]
        &= \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) P (M_B, x_1, c | z, m,\Omega_m, w, \alpha, \beta, \gamma, \delta\mathcal{Z}_b ) \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]
        &= \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) P (M_B, x_1, c, | \gamma) \delta(\hat{z} - z) \delta(\hat{m}-m)\\[10pt]
        &= \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) \delta(\hat{z} - z) \delta(\hat{m}-m) \\[10pt]

with

.. math::
    :label: j

    V &= \begin{pmatrix}
    \sigma_{M_B}^2                        & \rho_{12} \sigma_{M_B} \sigma_{x_1}         & \rho_{13} \sigma_{M_B} \sigma_{c}  \\
    \rho_{21} \sigma_{M_B} \sigma_{x_1}           & \sigma_{x_1}^2                    & \rho_{23} \sigma_{x_1} \sigma_{c}  \\
    \rho_{31} \sigma_{M_B} \sigma_{c}          & \rho_{32} \sigma_{x_1} \sigma_{c}       & \sigma_{c}^2  \\
    \end{pmatrix}

giving the population covariance.


.. note::
    In this implementation there is no skewness in the colour distribution.
    As we do not require normalised probabilities, we can simply add in correcting
    factors that can emulate skewness. This has been done in the ``simple_skew`` model, where we
    add in a CDF probability for the colour to turn our normal into a skew normal.

Putting this back together, we now have a simple hierarchical multi-normal model.
Adding in the priors, and taking into account that we observe multiple supernova, we have
that a final numerator of:



.. math::
    :label: k

    P(D_i|\theta) P(\theta) &\propto
    \rm{Cauchy}(\sigma_{M_B}|0,2.5)
    \rm{Cauchy}(\sigma_{x_1}|0,2.5)
    \rm{Cauchy}(\sigma_{c}|0,2.5)
    \rm{LKJ}(\rho|4) \\
    &\quad  \iiint d\eta_i \int M_{Bi}\
    \mathcal{N}\left( \hat{\eta_i} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta_i}}{\partial\mathcal{Z}_b} | \eta_i, C_i \right)
    \delta\left(M_{Bi} - \left[ m_{Bi} - \mu_i + \alpha x_{1i} - \beta c_i + k(z_i) m_i\right]\right) \\
    &\quad\quad\quad \mathcal{N}\left( \lbrace M_{Bi}, x_{1i}, c_i \rbrace |
    \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) \delta(\hat{z_i} - z_i) \delta(\hat{m_i}-m_i)

--------

Selection Effects
-----------------

Now, the easy part of the model is done, we need to move on to the real issue - our data is biased.
As the bias correction is not data dependent, but model parameter dependent (cosmology dependent),
the correction for each data point is identical, such that the correction for each individual supernova
is identical. I also note that, unlike the previous section, here we have to care about the
redshift and mass distributions, and so I will write them out.

We assume, for any given supernova, the selection effect can be determined as a function of apparent magnitude,
colour, stretch, redshift and mass. We might expect that the zero points have an effect
on selection efficiency, however this is because we normally consider zero points and
photon counts hand in hand. As we have a fixed experiment (fixed photon counts and statistics)
with different zero points, the selection efficiency is actually independent from zero points. Thus, we can
compute the bias correction as

.. math::
    :label: mmm

    w &= \idotsint d\hat{\eta} \, d\eta \, dz\, dm\, dM_B\
    \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}} | \eta, C \right)\   P(S|m_B, x_1, c, z, m) \\
    &\quad\quad\quad  \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right)\
    \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace |
    \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) P(z|\theta) \\

.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::
        :label: m

        w &= \iiint d\hat{\eta} \iiint d\eta \int dM_B\  \int d\hat{z} \int \hat{m} \int dz \int dm \,
        P(\hat{\eta},\eta, \hat{z},z, \hat{m},m, M_B|\theta) P(S|m_B, x_1, c, z, m)  \\[10pt]
        &= \idotsint d\hat{\eta} \, d\eta \, d\hat{z} \, dz\, d\hat{m}\, dm\, dM_B\
        \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}} | \eta, C \right)\   P(S|m_B, x_1, c, z, m)  \\
        &\quad\quad\quad  \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right)\
        \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace |
        \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)\delta(\hat{z} - z) \delta(\hat{m}-m) P(z|\theta) \\[10pt]
        &= \idotsint d\hat{\eta} \, d\eta \, dz\, dm\, dM_B\
        \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}} | \eta, C \right)\   P(S|m_B, x_1, c, z, m) \\
        &\quad\quad\quad  \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right)\
        \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace |
        \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) P(z|\theta)  \\

Again that we assume redshift and mass are perfectly known, so the relationship between
actual (latent) redshift and mass and the observed quantity is a delta function, hence why
they only appear once in the equation above. The important assumption
is that the detection efficiency is to good approximation
captured by the apparent magnitude, colour, stretch, mass and redshift of the supernova.

As we integrate over all possible realisations, we have that over all space

.. math::
    :label: n

    \iiint d\hat{\eta} \, P(\hat{\eta} | \eta, \delta\mathcal{Z}_b) =
    \iiint_{-\infty}^{\infty} d\hat{\eta}\,
    \mathcal{N}\left( \hat{\eta} + \delta\mathcal{Z}_b \frac{\partial\hat{\eta}}{\partial\mathcal{Z}} | \eta, C \right) = 1 \\

and as such we can remove it from the integral. As is expected, the final weight looks exactly like our likelihood,
except with some extra integral signs that marginalise over all possible experimental realisations:

.. math::
    :label: o

    w &= \idotsint d\eta\, dz \, dm \, dM_B\
    P(S|m_B, x_1, c, z, m)  \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) P(M_B, x_1, c | \gamma) P(z|\theta) \\

Addressing each component individually:

.. math::
    :label: p

    P(M_B, x_1, c|\gamma) &= \mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right) \\
    P(S|m_B, x_1, c, z, m)  &= \text{Probability of selection given actual underlying supernova values} \\
    \delta\left(M_B - \left[ m_B - \mu + \alpha x_1 - \beta c + k(z) m\right]\right) &= \text{Transformation function} \\
    P(z|\theta)   &= \text{Redshift distribution of supernova} \\

Finally, we note that, having :math:`N` supernova instead of one, we need only to normalise the likelihood
for each new point in parameter space, but not at each individual data point (because the normalisation
is independent of the data point). Thus our final posterior takes the following form, where I explicitly take into
account the number of supernova we have:

.. math::
    :label: final

    P(\theta|D) &\propto \frac{P(\theta)}{w^N} \idotsint d\vec{m_B}\, d\vec{x_1}\, \, d\vec{c}\, d\vec{M_B} \prod_{i=1}^N P(D_i|\theta) \\





.. note::
    :class: green

    **Technical aside**: Calculating :math:`P(S|m_B, x_1, c, z, m) `
    is not an analytic task. It has complications not just in the distance modulus being the
    result of an integral, but also that the colour and stretch correction factors make
    extra use of supernova specific values. The way to efficiently determine the efficiency
    is given as follows:

        1. Initially run a large DES-like simulation, recording all generated SN parameters and whether they pass the cuts.
        2. Using input cosmology to translate :math:`m_B, x_1, c` distribution to a :math:`M_B, x_1, c` distribution.
        3. Perform Monte-Carlo integration using the distribution.

    This gives our correction :math:`w` as

    .. math::
        :label: techw1

        w \propto \left[\sum_{\rm passed} \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace |
        \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}
        \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\, (P(z|\theta) dz)\, dm  \right]^N \\

    .. admonition:: Show/Hide derivation
        :class: toggle note math

        To go into the math, our Monte Carlo integration sample
        of simulated supernova is drawn from the multivariate normal distribution :math:`\mathcal{N}_{\rm sim}`.

        .. math::
            :label: techw2

            w^N &= \left[ \frac{1}{N_{\rm sim}} \sum  P(S|m_B, x_1, c, z,m)  \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}     \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\,(P(z|\theta) dz)\, dm  \right]^N \\
            &= \left[ \frac{1}{N_{\rm sim}} \sum_{\rm passed} \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}     \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\, (P(z|\theta) dz)\, dm  \right]^N \\
            &=  \frac{1}{N_{\rm sim}^N} \left[\sum_{\rm passed} \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}     \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\, (P(z|\theta) dz)\, dm  \right]^N

        As the weights do not have to be normalised, we can discard the constant factor out front. We also note that
        determining whether a simulated supernova has passed the cut now means converting light curve counts to flux
        and checking that the new fluxes pass signal-to-noise cuts.

        .. math::
            :label: techw3

            w^N &\propto  \left[\sum_{\rm passed} \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}     \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\, (P(z|\theta) dz)\, dm  \right]^N \\
            \log\left(w^N\right) - {\rm const} &=  N \log\left[\sum_{\rm passed} \frac{\mathcal{N}\left( \lbrace M_B, x_1, c \rbrace | \lbrace \langle M_B \rangle, \langle x_1 \rangle, \langle c \rangle \rbrace, V \right)}{\mathcal{N}_{\rm sim}}     \left( \mathcal{N}_{\rm sim} dm_B\,d x_1\, d_c \right)\, (P(z|\theta) dz)\, dm  \right]

        Given a set of points to use in the integration, we can see that subtracting the above
        term from our log-likelihood provides an implementation of our bias correction.

.. warning::
    A primary concern with selection effects is that they grow exponentially worse with
    more data. To intuitively understand this, if you have an increased number of (biased)
    data points, the posterior maximum becomes better constrained and you need an increased
    re-weighting (bias correction) to shift the posterior maximum to the correct location. Because
    of this, we will need to implement an approximate bias correction in Stan.


To recap, we have a full bias correction that can be computed using Monte-Carlo integration. However,
Monte-Carlo integration cannot be put inside the Stan framework, and having no bias correction
at all in the Stan framework means that our sampling efficiency drops to close to zero, which makes
it very difficult to adequately sample the posterior adequately. As such, we need an approximate
bias correction which *can* go inside Stan to improve our efficiency.

We can do this by looking at the selection efficiency simply as
a function of apparent magnitude for the supernova. There are two possibilities that we can do. The first
is to approximate the selection efficiency as a normal CDF, as was done in Rubin (2005). However, when
simulating the DES data, low spectroscopic efficiency at brighter magnitudes makes a CDF an inappropriate
choice. Instead, the most general analytic form we can prescribe the approximate correction
would be using a skew normal, as (depending on the value of the skew parameter :math:`\alpha`) we
can smoothly transition from a normal CDF to a normal PDF. Thus the approximate bias function
is described by

.. math::
    :label: approxbiassmall

    w_{\rm approx} &= \int dz \left[ \int dm_B \,  S(m_B) P(m_B|z,\theta) \right] P(z|\theta) \\[10pt]

.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::
        :label: approxbias

        w_{\rm approx} &= \int d\hat{z} \int d\hat{m_B} \, P(\hat{z},\hat{m_B}|\theta) S(m_B) \\[10pt]
        &= \int d\hat{z} \int d\hat{m_B} \int dz \int dm_B \, P(\hat{z},\hat{m_B},z,m_B|\theta)  S(m_B) \\[10pt]
        &= \int d\hat{z} \int d\hat{m_B} \int dz \int dm_B \, P(\hat{z}|z) P(\hat{m_B}|m_B) P(m_B|z,\theta) P(z|\theta)  S(m_B) \\[10pt]
        &= \int d\hat{z} \int d\hat{m_B} \int dz \int dm_B \, \delta(\hat{z}-z) \mathcal{N}(\hat{m_B}|m_B,\hat{\sigma_{m_B}}) P(m_B|z,\theta) P(z|\theta)  S(m_B) \\[10pt]
        &= \int dz \int dm_B \, \left[ \int d\hat{m_B} \mathcal{N}(\hat{m_B}|m_B,\hat{\sigma_{m_B}}) \right] P(m_B|z,\theta) P(z|\theta) S(m_B) \\[10pt]
        &= \int dz \left[ \int dm_B \,  S(m_B) P(m_B|z,\theta) \right] P(z|\theta) \\[10pt]



As such, we have our efficiency function

.. math::
    :label: ee1

    S(m_B) = \mathcal{N}_{\rm skew} (m_B | m_{B,{\rm eff}}, \sigma_{{\rm eff}}, \alpha_{\rm eff})\\

With our survey efficiency thus defined, we need to describe our supernova model as a population
in apparent magnitude (and redshift). This will be given by a normal function with mean
:math:`m_B^*(z) = \langle M_B \rangle + \mu(z) - \alpha \langle x_1 \rangle + \beta \langle c \rangle`.
The width of this normal is then given by
:math:`(\sigma_{m_B}^*)^2 = \sigma_{m_B}^2 + (\alpha \sigma_{x_1})^2 + (\beta \sigma_c)^2 + 2(\beta \sigma_{m_B,c} -\alpha \sigma_{m_B,x_1} - \alpha\beta\sigma_{x_1,c})`,
such that we formally have

.. math::
    :label: poppdf

    P(m_B | z,\theta) &= \mathcal{N}(m_B | m_B^*(z), \sigma_{m_B}^*) \\

From this, we can derive an approximate weight :math:`w_{\rm approx}`:

.. math::
    :label: wstarshort

    w_{\rm approx} &= 2 \int dz \,
    \mathcal{N} \left( \frac{ m_{B,{\rm eff}} - m_B^*(z) }{ \sqrt{ \sigma_{{\rm eff}}^2 + \sigma_{m_B}^{*2} }} \right)
    \Phi\left( \frac{ {\rm sign}(\alpha) \left( m_B^*(z) - m_{B,{\rm eff}} \right) }{ \frac{\sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2}{\sigma_{{\rm eff}}^2} \sqrt{ \left( \frac{ \sigma_{{\rm eff}} }{ \alpha_{\rm eff} }  \right)^2 +      \frac{  \sigma_{m_B}^{*2} \sigma_{{\rm eff}}^2  }{ \sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2 }        } }  \right)
    P(z|\theta) \\[10pt]


.. admonition:: Show/Hide derivation
   :class: toggle note math

    .. math::
        :label: wstar

        w_{\rm approx} &= \int dz \left[ \int dm_B \,  S(m_B) P(m_B|z,\theta) \right] P(z|\theta) \\[10pt]
        &= \int dz \left[
        \int dm_B \,  \mathcal{N}_{\rm skew} (m_B | m_{B,{\rm eff}}, \sigma_{{\rm eff}}, \alpha_{\rm eff})
        \mathcal{N}(m_B | m_B^*(z), \sigma_{m_B}^*)
        \right] P(z|\theta) \\[10pt]
        &= 2 \int dz \left[
        \int dm_B \,  \mathcal{N} \left(\frac{m_B - m_{B,{\rm eff}}}{\sigma_{{\rm eff}}}\right) \Phi\left(\alpha_{\rm eff} \frac{m_B - m_{B,{\rm eff}}}{\sigma_{{\rm eff}}}\right)
        \mathcal{N}\left(\frac{m_B - m_B^*(z)}{\sigma_{m_B}^*}\right)
        \right] P(z|\theta) \\[10pt]
        &= 2 \int dz \left[ \int dm_B \,
        \mathcal{N} \left( \frac{ m_{B,{\rm eff}} - m_B^*(z) }{ \sqrt{ \sigma_{{\rm eff}}^2 + \sigma_{m_B}^{*2} }} \right)
        \mathcal{N} \left( \frac{ m_B - \bar{m_B} }{  \bar{\sigma}_{m_B}  }\right)
        \Phi\left(\alpha_{\rm eff} \frac{m_B - m_{B,{\rm eff}}}{\sigma_{{\rm eff}}}\right)
        \right] P(z|\theta) \\[10pt]
        & {\rm where }\ \  \bar{m_B} = \left( m_{B,{\rm eff}} \sigma_{m_B}^{*2} +   m_B^*(z) \sigma_{{\rm eff}}^2 \right) / \left( \sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2 \right)  \\[10pt]
        & {\rm where }\ \  \bar{\sigma}_{m_B}^2 = \left(  \sigma_{m_B}^{*2} \sigma_{{\rm eff}}^2  \right) / \left( \sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2 \right)   \\[10pt]
        &= 2 \int dz \,
        \mathcal{N} \left( \frac{ m_{B,{\rm eff}} - m_B^*(z) }{ \sqrt{ \sigma_{{\rm eff}}^2 + \sigma_{m_B}^{*2} }} \right)
        \left[ \int dm_B \,
        \mathcal{N} \left( \frac{ m_B - \bar{m_B} }{  \bar{\sigma}_{m_B}  }\right)
        \Phi\left(\alpha_{\rm eff} \frac{m_B - m_{B,{\rm eff}}}{\sigma_{{\rm eff}}}\right)
        \right] P(z|\theta) \\[10pt]
        &= 2 \int dz \,
        \mathcal{N} \left( \frac{ m_{B,{\rm eff}} - m_B^*(z) }{ \sqrt{ \sigma_{{\rm eff}}^2 + \sigma_{m_B}^{*2} }} \right)
        \Phi\left( \frac{{\rm sign}(\alpha) \left( \bar{m_B} - m_{B,{\rm eff}} \right)}{ \sqrt{ \left( \frac{ \sigma_{{\rm eff}} }{ \alpha_{\rm eff} }  \right)^2 + \bar{\sigma}_{m_B}^2 } }  \right)
        P(z|\theta) \\[10pt]
        &= 2 \int dz \,
        \mathcal{N} \left( \frac{ m_{B,{\rm eff}} - m_B^*(z) }{ \sqrt{ \sigma_{{\rm eff}}^2 + \sigma_{m_B}^{*2} }} \right)
        \Phi\left( \frac{ {\rm sign}(\alpha) \left(  m_B^*(z) - m_{B,{\rm eff}} \right) }{ \frac{\sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2}{\sigma_{{\rm eff}}^2} \sqrt{ \left( \frac{ \sigma_{{\rm eff}} }{ \alpha_{\rm eff} }  \right)^2 +      \frac{  \sigma_{m_B}^{*2} \sigma_{{\rm eff}}^2  }{ \sigma_{m_B}^{*2} +  \sigma_{{\rm eff}}^2 }        } }  \right)
        P(z|\theta) \\[10pt]


    `Thank you Wikipedia for laying out the second last line out so nicely <https://en.wikipedia.org/wiki/Error_function#Integral_of_error_function_with_Gaussian_density_function>`_.

We can see here that as our skew normal approaches a normal (:math:`\alpha \rightarrow 0`), the CDF function tends to
:math:`\frac{1}{2}` and gives us only the expected normal residual.


.. note::

    If we wanted to use the original complimentary CDF approximation for the selection efficiency, we would get the integral
    of the complimentary CDF function.

    .. math::
        :label: wstarshort2

        w_{\rm approx} &= 2 \int dz \,
        \Phi^c\left( \frac{m_B^* - m_{B,{\rm eff}}}{\sqrt{ {\sigma_{m_B}^*}^2 +   \sigma_{{\rm survey}}^2}} \right)
        P(z|\theta) \\[10pt]

    Now here we depart from Rubin (2015). Rubin (2015) formulate their likelihood in terms of a combinatorial
    problem, taking into account the number of observed events and an unknown number of missed events. Detailed in
    their Appendix B, they also make "the counterintuitive approximation that the redshift of each missed
    SN is exactly equal to the redshift of a detected SN. This approximation is accurate because the SN samples have,
    on average, enough SNe that the redshift distribution is reasonable sampled."

    Unfortunately, I must disagree that this approximation is valid, because
    whilst the SN surveys *may* be able to reasonable sample the *observed* redshift distribution of SN, they
    *do not* adequately sample the underlying redshift distribution, which is important in my formulation.

    Now, the underlying redshift distribution goes to a very high redshift,
    however we note that we would not have to integrate over all of it, because
    above the observed redshift distribution the contribution to the integral quickly drops to zero. However,
    sampling the high redshift tail is still necessary.

    It is of interest that the difference in methodology (between my integral and Rubin's
    combinatorics/redshift approximation/geometric series) leads to the following difference in bias corrections.

    Note that I use capital W below, to denote a correction for the entire model, not a single supernova.

    .. math::
        W_{\rm approx} &= 2 \left(\int dz \,
        \Phi^c\left( \frac{m_B^* - m_{B,{\rm eff}}}{\sqrt{ {\sigma_{m_B}^*}^2 +   \sigma_{{\rm survey}}^2}} \right)
        P(z|\theta) \right)^N \\[10pt]
        W_{\rm Rubin} &= \prod_{i=1}^N \frac{P({\rm detect}|\lbrace \hat{m_{Bi}}, \hat{x_{1i}}, \hat{c_i} \rbrace) }{P({\rm detect} | z_i) }
        = \prod_{i=1}^N (\epsilon + P({\rm detect} | z_i))^{-1} \\

    where the last line utilises a small :math:`\epsilon` to aid convergences, and we discard the
    numerator as Rubin states with :math:`\epsilon > 0` it didn't turn out to be important.

    To try and compare these different methods, I've also tried a similar exact redshift approximation
    to reduce my integral down to a product, however it does not work well.


After fitting the above posterior surface, we can remove the approximation correction
and implement the actual Monte Carlo correction by assigning each point the chain the weight based on the
difference between the approximate weight and the actual weight.


Final Model
-----------

From the mathematics laid out before, I test three models. 

For the first model, as the hostmass distribution and redshift
distribution are not well known, I keep mass and redshift as top level model parameters.
With this, I adopt the assumption of the redshift distribution being well sampled, and apply only the
approximate correction. As such, this will allow me to get a reference for the other two models.

The second and third models have mass and redshift coming from a parent population. The two models
are when applying the full Monte-Carlo correction and when not (keeping it only the approximate 
correction).

To test the models, I have multiple datasets I test them on. The `simple` dataset is one constructed
by hand with simple draws and a perfect selection effect. The SNANA datasets use SNANA and thus
have proper selection effects which are not perfectly skew normal. There are multiple realisations
of :math:`\Omega_m`, and a simulation which introduces a skewed colour distribution (bifurcated gaussian 
population).

.. figure::     ../dessn/configurations/plots/approximate_simple_test.png
    :align:     center
    :width:     100%

    Approx simple test, looks good.

.. figure::     ../dessn/configurations/plots/full_simple_test.png
    :align:     center
    :width:     100%

    Full simple test, concerns over :math:`\Omega_m` when applying the full correction.

.. figure::     ../dessn/configurations/plots/approximate_snana_array_test.png
    :align:     center
    :width:     100%

    Approximate SNANA tests. Looks good. The underestimation of :math:`\sigma` is from SNANA adding
    extra uncertainty, and the outlier :math:`\sigma_c` from the skewed test is because the bifurcated
    gaussian has width 0.1 and 0.05, so 0.75 is the correct value for that dataset.

.. figure::     ../dessn/configurations/plots/full_snana_array_test.png
    :align:     center
    :width:     100%

    Full SNANA tests. Looks good, as above.



------------------

|
|
|
|
|
|
|
|
|

Appendix 1 - MC inside Stan
---------------------------

.. warning::

    Given the concerns with the importance sampling methods, I also decided to implement
    the bias corrections within STAN itself - that is, have Stan perform rough Monte-Carlo
    integration to get the bias correction in explicitly. Inserting the relevant data and structures
    into STAN such that I can perform Monte Carlo integration in a BHM framework significantly
    slows down the fits, however I believed it would at least give good results.

    In addition to the odd contours, we I also see in the walk itself that we have
    sampling issues, with some walkers sampling some areas of posterior space more than others.
    Stan's lack of convergence here is a big issue, indicating that the surfaces adding MC integration
    creates are intractable to Stan.



Appendix 2 - Gaussian Processes
-------------------------------

.. warning::

    As performing Monte Carlo integration inside Stan hit a dead end, I decided to investigate
    if I could achieve an approximate solution by using Gaussian Processes. Unfortunately,
    what we can see happneing in the plots below is that a single point of in the GP has a substantially
    higher weight than the others (a presumed combination of stochastic randomness
    and being in an unusual area of parameter space). However, this meant that any walker
    randomly initialised near this point would be stuck to it. Even if this did not happen,
    viewing the other walkers revealed issues with them preferring matter densities as high as
    possible, which is obviously not what is wanted. It seems that without a huge number of points
    (which Stan cannot do) our model is too high-dimensional that we cannot use a Gaussian Process.



Appendix 2 - Nearest Point GP
-----------------------------

.. warning::

    Building off a regular Gaussian Process, the high dimensionality of our model
    may be causing difficulties due to the GP kernel - if we are averaging or blending
    over too many points (too great a volume in parameter space), we would not expect
    accurate results. To test if this was the issue, I increased the number of points
    in the GP to a high value (in the thousands), and then modified the distance metric
    used to calculate the kernel - raising it to a power and then normalising, such
    that the distance to the closest point approached one, and the distance to all
    other points approached infinity (or really a number much larger than one).

    By doing this - instead of fitting the GP hyper parameters - I have essentially
    created a smooth, infinitely-differentiable nearest-point-interpolator. But, looking at
    the results below, apparently that is exactly what I don't want!

    Whats is actually happening is that Stan uses a Hamiltonian Monte Carlo algorithm, which
    takes into account the gradient of the posterior surface. The nearest-point GP setup I
    am using has extreme gradients because the GP values quickly shift when you cross the equidistant
    threshold between two points. These extreme gradients, and the convoluted and chaotic boundaries
    given by the equidistant constraint on a thousand points in high dimensional volume, completely
    breaks Stan's HMC algorithm.

"""