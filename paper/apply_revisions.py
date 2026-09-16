"""Applies the reviewer-response edits to paper_submitted.tex -> paper.tex"""
s=open('paper_submitted.tex').read()
def R(old,new):
    global s
    assert s.count(old)==1, old[:80]
    s=s.replace(old,new)

R("achieving 42.5\\% renewable penetration. A post-hoc distributionally robust assessment evaluates hurricane resilience,",
  "achieving 42.5\\% renewable penetration; Trinidad's gas-anchored optimum builds no new RE, and a sensitivity analysis shows solar entering at gas costs above \\$65--70/MWh, a carbon price of \\$25--50/tCO$_2$, or solar CAPEX of \\$800/kW. A post-hoc distributionally robust stress test evaluates hurricane resilience,")

old_dro=s[s.index("\\subsection{Post-Hoc DRO Resilience}"):s.index("% ══════════════════════════════════════════════════════\n\\section{Case Studies}")]
new_dro=r"""\subsection{Post-Hoc DRO Resilience}

Hurricane resilience is assessed outside the optimization as a stylized distributionally robust stress test. For island~$i$, each Saffir--Simpson category $c\in\{1,\dots,5\}$ has a damage profile $(p_c, g_c, h_c)$: base share of hurricanes $p_c$, fractional grid outage $g_c$, and outage duration $h_c$\,(h). The annual event rate is $\lambda_{i,c}=s_i p_c$, where $s_i$ is an island exposure multiplier. Unserved DC energy per event is
\begin{equation}
\text{UE}_{i,c}=\bigl[P_i^{\text{DC}}h_c-0.5(1-g_c)P_i^{\text{DC}}h_c-E_i^{\text{BTM}}(1-0.3g_c)\bigr]^{+}
\label{eq:ue}
\end{equation}
assuming 50\% residual grid supply on non-outaged feeders and BTM availability derated by $0.3g_c$. Resilience is
\begin{equation}
R_i(\varepsilon) = 1 - \frac{\sum_c \tilde{\lambda}_{i,c}(\varepsilon)\,\text{UE}_{i,c}}{P_i^{\text{DC}} \cdot 8760},\quad \tilde{\lambda}_{i,c}=\bigl[s_i p_c+\varepsilon(2g_c-0.5)\bigr]_{0.001}^{0.999}
\label{eq:dro}
\end{equation}
The adversarial tilt moves frequency from low-outage toward high-outage categories as $\varepsilon$ grows. It is a tractable surrogate for the worst case over a Wasserstein ball on the category distribution, not an exact DRO solution.

\textit{Parameter basis}: $p_c=(0.35,0.25,0.20,0.15,0.05)$ is set to be broadly consistent with the peak-intensity distribution of Atlantic hurricanes in NOAA HURDAT2~\cite{hurdat2}. $g_c$ (0.15--0.90) and $h_c$ (24--240\,h) are engineering judgement, not fitted to utility outage records. $s_{\text{Trinidad}}=0.3$ and $s_{\text{Jamaica}}=0.8$ reflect Trinidad's position at the southern margin of the Atlantic hurricane track (${\approx}10.5^\circ$N) relative to Jamaica. The radius range $\varepsilon\in[0,0.20]$ is a sensitivity sweep rather than an estimate; it represents a plausible shift toward intense storms, consistent in direction with projected increases in the proportion of Category~4--5 cyclones~\cite{ipcc_ar6}. $E^{\text{BTM}}$ equals the modeled BTM capacity (30/84\,MWh). All values are illustrative; calibration against JPS and T\&TEC restoration records is future work.

"""
s=s.replace(old_dro,new_dro)

R(r"""\textbf{Trinidad}: The optimizer deploys Brechin Castle's 92\,MW solar output (1.8\% RE fraction) but builds no additional RE or storage. The existing gas fleet serves the 5\,MW DC and national demand at competitive marginal cost. This outcome reflects the current economic reality of Trinidad's energy system, where abundant domestic gas provides reliable, low-cost baseload. Importantly, however, the framework could be applied to scenario analyses exploring future conditions---such as evolving gas allocation strategies or expanded RE targets---where additional solar and storage investment may become economically attractive.""",
r"""\textbf{Trinidad}: The optimizer dispatches Brechin Castle's 92\,MW (1.8\% RE fraction) but builds no additional RE or storage. At a gas cost of \$55/MWh, new solar (levelized ${\approx}$\$67/MWh at 7\% WACC and CF\,0.18) is not competitive.

\textit{Robustness}: Table~\ref{tab:sens} varies gas cost, carbon price, and solar CAPEX one at a time. The response is a threshold. Solar enters between \$65 and \$70/MWh gas cost, at a carbon price between \$25 and \$50/tCO$_2$ (equivalent to a \$9--19/MWh adder at 0.37\,tCO$_2$/MWh), or at \$800/kW solar CAPEX. When it enters, all 300\,MW of candidate solar is built, and wind follows at \$100/MWh. RE rises only to 7.5--9.9\% and CO$_2$ falls by 6--8\%. Storage and BTM never deploy in the tested range. Two features limit uptake: the candidate capacity caps and the 25\% minimum stable output of the 1{,}800\,MW gas fleet. The zero-RE result is therefore robust at current gas costs but sensitive to modest carbon pricing or cost declines.

\begin{table}[htbp]
\centering
\caption{Case A Sensitivity (one-at-a-time; base: gas \$55/MWh, solar \$1{,}100/kW, no carbon price)}
\label{tab:sens}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccccc@{}}
\toprule
Scenario & New PV & New wind & RE & Cost & CO$_2$ \\
 & (MW) & (MW) & (\%) & (M\$/yr) & (kt/yr) \\
\midrule
Base & 0 & 0 & 1.8 & 443 & 2{,}983 \\
Gas \$45--65/MWh & 0 & 0 & 1.8 & 363--524 & 2{,}983 \\
Gas \$70/MWh & 300 & 0 & 7.5 & 563 & 2{,}808 \\
Gas \$85/MWh & 300 & 0 & 7.5 & 677 & 2{,}808 \\
Gas \$100/MWh & 300 & 100 & 9.9 & 791 & 2{,}737 \\
CO$_2$ \$25/t & 0 & 0 & 1.8 & 518 & 2{,}983 \\
CO$_2$ \$50/t & 300 & 0 & 7.5 & 590 & 2{,}808 \\
Solar \$800/kW & 300 & 0 & 7.5 & 442 & 2{,}808 \\
\bottomrule
\end{tabular}
\end{table}""")

R(r"""\textbf{Jamaica}: The optimizer aggressively deploys 405\,MW solar (maxing May Pen and Old Harbour caps) and 278\,MW wind at Montego Bay, with 800\,MWh grid BESS at Kingston and Old Harbour. Notably, 84\,MWh BTM BESS deploys at the Kingston DC bus. BTM deployment is driven by transmission congestion: during peak coincident DC and grid demand, the KGN--OH corridor (300\,MW) constrains RE imports from central parishes, making local storage at the DC bus economically justified. Jamaica's 42.5\% RE aligns with its government's 50\% by 2030 target.""",
r"""\textbf{Jamaica}: The optimizer deploys 405\,MW solar across May Pen and Old Harbour and 278\,MW wind at Montego Bay. Grid BESS reaches its 800\,MWh build limit at Kingston and Old Harbour, and 84\,MWh BTM BESS deploys at the Kingston DC bus, also at its limit. BTM is chosen despite its cost premium because the grid-BESS limits bind. A copper-plate rerun (unconstrained, lossless transmission) deploys the same storage (800\,MWh grid, 84\,MWh BTM), 400\,MW solar, and 281\,MW wind, at \$507M/yr (0.8\% lower). The 4-bus network is congested for only 54\,h (MP$\rightarrow$OH) and 13\,h (OH$\rightarrow$KGN) of 2{,}190\,h. Storage deployment is therefore driven by solar variability and the storage build limits rather than by transmission congestion. The 42.5\% Q1 RE share is consistent with Jamaica's 50\%-by-2030 target.""")

R(r"""\textbf{DRO Resilience}: Trinidad maintains $R > 0.988$ across all Wasserstein radii due to its position south of the main hurricane belt (10.5$^\circ$N) and diverse generation. Jamaica degrades from $R = 0.995$ to $R = 0.970$ at $\varepsilon = 0.20$, driven by wind asset vulnerability. The 84\,MWh BTM provides approximately 4~hours of islanded DC backup.""",
r"""\textbf{DRO Resilience}: Trinidad remains at $R \geq 0.989$ ($0.998\rightarrow0.989$) across $\varepsilon\in[0,0.20]$, reflecting its low exposure multiplier. Jamaica degrades from $R = 0.996$ to $R = 0.987$ at $\varepsilon = 0.20$, driven by higher strike exposure. In both cases the BTM provides about 4~hours of islanded DC backup at full load (84\,MWh for a 21\,MW facility load in Jamaica). These values inherit the illustrative parameters of Section~III-D and should be read comparatively, not as absolute availability estimates.""")

R(r"""We propose a 10-factor framework calibrated to Caribbean conditions (Table~\ref{tab:siting}).""",
r"""We propose a 10-factor framework for Caribbean conditions (Table~\ref{tab:siting}). The current version is an \emph{expert-elicited prototype}. The authors assigned scores against the anchors in Table~\ref{tab:rubric}, using the LP results (grid headroom, transmission), the cost and resource assumptions of Section~IV (RE quality), and public infrastructure and hazard information. Scores are unweighted and have not yet been validated with stakeholders; formal MCDA is planned (Section~VII).

\begin{table}[htbp]
\centering
\caption{Scoring Anchors for Table~\ref{tab:siting} (Prototype)}
\label{tab:rubric}
\scriptsize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{@{}p{1.9cm}p{3.1cm}p{3.1cm}@{}}
\toprule
Factor & Score 5 & Score 1 \\
\midrule
Grid headroom & Large reserve margin; DC ${<}1\%$ of peak & Tight margin; DC ${>}5\%$ of peak \\
RE resource & Solar CF ${\geq}0.21$ or wind CF ${\geq}0.30$ nearby & Weak resource, little buildable land \\
Transmission & HV substation on site; no congestion & New HV line or congested corridor \\
Fibre RTT & ${<}30$\,ms to Miami, diverse cables & ${>}60$\,ms or single cable \\
IX/peering & IXP in same metro & No domestic IXP nearby \\
Hurricane & Rarely on track; outside surge zone & Frequent major-storm track; coastal \\
Water & Unstressed or non-potable source & Stressed municipal supply only \\
Seismic & Low hazard zone & High hazard; near active fault \\
Noise buffer & ${\geq}150$\,m to residences feasible & Residences ${<}50$\,m \\
Zoning & Heavy-industrial zoning permits use & Rezoning and full EIA needed \\
\bottomrule
\end{tabular}
\end{table}""")

R(r"""No carbon price or emission constraint is modeled.""",
  r"""Carbon pricing is examined only as a one-at-a-time sensitivity for Trinidad (Table~\ref{tab:sens}); no emission constraint is modeled.""")
R(r"""The 10-factor framework uses expert-assigned scores rather than quantitative indices with defined rubrics. Weighting is uniform, yet""",
  r"""The 10-factor framework uses expert-assigned scores guided by qualitative anchors (Table~\ref{tab:rubric}) rather than quantitative indices. Weighting is uniform, yet""")
R("We identify five categories of weakness","We identify six categories of weakness")

R(r"""\textit{Why this work matters for Caribbean SIDS}: No published study applies open-source capacity expansion modeling to data center co-planning in the Caribbean. The combination of PyPSA optimization with a societal siting framework addresses a gap where existing tools focus exclusively on either energy economics (HOMER, PLEXOS) or real estate considerations (CBRE, JLL reports), but never both. For SIDS policymakers evaluating data center proposals---which increasingly arrive as unsolicited foreign direct investment---the framework provides a transparent, reproducible, and license-free assessment methodology that does not require commercial software procurement or external consulting fees.""",
r"""\textit{Why this work matters for Caribbean SIDS}: We are not aware of a published study that applies open-source capacity expansion modeling to data center co-planning in the Caribbean. Existing tools address energy economics (HOMER, PLEXOS) or real estate (CBRE, JLL) separately. For SIDS policymakers assessing data center proposals, which often arrive as unsolicited foreign investment, the framework offers a transparent, license-free assessment.""")
R(r"""\textit{Transmission reveals what single-bus hides}: Jamaica's 4-bus model shows RE concentrating at May Pen (solar) and Montego Bay (wind) while DC demand sits at Kingston. The MP--MB corridor (180\,MW, 100\,km through mountainous terrain) is the binding constraint, explaining why 800\,MWh of grid BESS deploys at Kingston and Old Harbour rather than at RE-rich buses. In a single-bus (copper-plate) model, this congestion is invisible, BTM BESS never deploys, and the total system cost is underestimated. This finding has direct implications for Jamaica's IRP-2 process, which uses simplified single-bus models for some analyses.""",
r"""\textit{What the network adds}: In Jamaica, RE concentrates at May Pen and Montego Bay while the DC load sits at Kingston. At the present 138\,kV ratings, however, the copper-plate comparison changes cost by only 0.8\% and leaves storage unchanged. The multi-bus model is still necessary to confirm this, and it becomes decisive under larger DC loads or corridor outages (N-1). These cases are the natural next test for IRP-type studies.""")
R(r"""\textit{The Brechin Castle model for SIDS}: Trinidad's Brechin Castle project---a bp/Shell/NGC joint venture delivering 92\,MWac on 186~hectares---demonstrates a replicable model for Caribbean RE deployment. The consortium structure, with international energy companies partnering a national gas company and government facilitation without direct equity, addresses the financing and technical capacity constraints that impede utility-scale RE in smaller SIDS~\cite{brechin_ecp}. A data center co-located at Point Lisas could leverage both the existing industrial zoning and the adjacent solar generation, reducing the need for long-distance transmission.""",
r"""\textit{The Brechin Castle model for SIDS}: The bp/Shell/NGC consortium behind Brechin Castle pairs international developers with a national gas company under government facilitation. This structure addresses the financing and capacity constraints facing utility-scale RE in smaller SIDS~\cite{brechin_ecp}. A Point Lisas data center could combine existing industrial zoning with the adjacent solar. Table~\ref{tab:sens}, however, shows that additional RE there depends on gas pricing or carbon policy.""")
R(r"""\textit{Societal factors dominate SIDS siting}: On small islands, a 500-foot setback requirement---now standard in Virginia~\cite{stafford2025}---may consume a significant fraction of available industrial land. In Dominica or St.~Kitts, such a buffer could extend across the entire width of a coastal settlement. Even in Jamaica (10{,}990\,km$^2$), industrial zones are concentrated in a few corridors. The Point Lisas Industrial Estate in Trinidad and Old Harbour in Jamaica offer rare exceptions where heavy industrial zoning with adequate buffer zones already exists. Future Caribbean DC development should prioritize such brownfield sites rather than greenfield development that would require new zoning frameworks.""",
r"""\textit{Societal factors dominate SIDS siting}: A 500-foot setback, now adopted in parts of Virginia~\cite{stafford2025}, could span an entire coastal settlement in Dominica or St.~Kitts. Even in Jamaica, industrial land is confined to a few corridors. Point Lisas and Old Harbour are rare brownfield sites with heavy-industrial zoning and room for buffers, and they should be prioritized over greenfield sites that require new zoning.""")

R(r"""Jamaica's 4-bus model, grounded in real JPS topology, deploys 84\,MWh BTM BESS at the DC bus due to transmission congestion---a result invisible in single-bus analysis.""",
  r"""Jamaica's 4-bus model, grounded in JPS topology, reaches 42.5\% RE with 800\,MWh grid BESS and 84\,MWh BTM BESS. A copper-plate comparison shows that storage deployment there is driven by storage build limits rather than congestion. For Trinidad, sensitivity analysis shows the zero-new-RE optimum reverses at moderate carbon prices (\$25--50/tCO$_2$) or solar CAPEX near \$800/kW.""")
R(r"""(iv)~incorporation of carbon pricing and NDC emission constraints""", r"""(iv)~calibration of hurricane damage parameters to utility outage records, and full carbon pricing and NDC emission constraints""")
R(r"""\bibitem{irena2023}""", r"""\bibitem{hurdat2} C.~W. Landsea and J.~L. Franklin, ``Atlantic hurricane database uncertainty and presentation of a new database format,'' \textit{Mon.\ Weather Rev.}, vol.~141, pp.~3576--3592, 2013.

\bibitem{ipcc_ar6} S.~I. Seneviratne \textit{et al.}, ``Weather and climate extreme events in a changing climate,'' in \textit{Climate Change 2021: The Physical Science Basis}, IPCC AR6 WG1, Ch.~11, Cambridge Univ.\ Press, 2021.

\bibitem{irena2023}""")
open('paper.tex','w').write(s)
print("ok")

# --- page-budget trims (keep 6 pages) ---
s=open('paper.tex').read()
a=s.index("\\section*{Acknowledgments}"); b=s.index("\\balance")
s=s[:a]+"\\section*{Acknowledgments}\n\nThe authors thank the PyPSA~\\cite{pypsa} and HiGHS~\\cite{highs} developers for open-source tools that make energy system modeling accessible to SIDS researchers.\n\n"+s[b:]
i=s.index("\\bibitem{tt_energy2024}"); j=s.index("\\bibitem{uli2024}"); s=s[:i]+s[j:]
old=s[s.index("PyPSA~\\cite{pypsa} was selected for its combination of:"):s.index("\n",s.index("PyPSA~\\cite{pypsa} was selected for its combination of:"))]
s=s.replace(old,"PyPSA~\\cite{pypsa} was selected because it is MIT-licensed, models multi-bus networks with transmission constraints natively, runs with the open-source HiGHS solver~\\cite{highs}, and is backed by an active community and the global PyPSA-Earth model~\\cite{pypsa_earth}. Its Python API scales from single-bus to continental networks, covering both case studies here.")
open('paper.tex','w').write(s)
